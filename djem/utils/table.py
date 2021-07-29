import shutil
import textwrap

from django.utils.encoding import force_text


class NOT_PROVIDED:
    pass


class RowWrapper:
    """
    Helper class for formatting full-width rows such as titles, descriptions and
    footers.
    """
    
    ALIGN_MAP = {
        'left': 'ljust',
        'right': 'rjust',
        'center': 'center',
        'centre': 'center'
    }
    
    def __init__(self, value, alignment='left'):
        
        self.raw_value = value
        self.set_alignment(alignment)
    
    def set_alignment(self, alignment):
        
        try:
            self._align = self.ALIGN_MAP[alignment]
        except KeyError:
            self._align = 'ljust'
    
    def get_rows(self, table_width):
        
        rows = []
        
        # Subtract 4 from the table width to account for the "| " and " |"
        table_width -= 4
        
        # Split value into multiple rows based on line breaks. Wrap any of the
        # rows that are longer than the shortened table width, and align them
        # within that width.
        for line in self.raw_value.split('\n'):
            for sub_line in textwrap.wrap(line, table_width):
                rows.append('| {0} |'.format(
                    getattr(sub_line, self._align)(table_width)
                ))
        
        return rows


class Table:
    
    class FULL_WIDTH:
        """
        Max width constant indicating the full width of the terminal.
        """
        
        pass
    
    class BR:
        """
        Row constant representing a blank row.
        """
        
        pass
    
    class HR:
        """
        Row constant representing a horizontal rule.
        """
        
        pass
    
    MIN_COLUMN_WIDTH = 4  # allows for a single character and "..." to indicate truncation
    
    def __init__(self, headings=None, title=None, footer=None, max_width=FULL_WIDTH):
        
        self._rows = []
        self._columns = []
        
        if headings:
            self.add_headings(headings)
        else:
            self._headings = None
        
        if title:
            self.set_title(title)
        else:
            self.title = None
        
        if footer:
            self.set_footer(footer)
        else:
            self.footer = None
        
        self._raw_max_width = max_width
    
    def _update_col_metadata(self, col_data, value=NOT_PROVIDED, heading=NOT_PROVIDED):
        
        if value is not NOT_PROVIDED:
            width = len(force_text(value))
        elif heading is not NOT_PROVIDED:
            heading = force_text(heading)
            width = 0
            
            col_data['heading'] = heading
        else:
            raise TypeError('Invalid arguments provided.')
        
        if width > col_data.get('raw_width', 0):
            col_data['raw_width'] = width
        
        return col_data
    
    def _reduce_column_widths(self, reduction, width_map):
        
        # Reduce the widths of each column until the overall table width no
        # longer exceeds the maximum. Target the widest columns first. When
        # multiple columns share the same width, target those that come later
        # in the table.
        sorted_widths = sorted(width_map.keys(), reverse=True)
        
        for i, col_width in enumerate(sorted_widths):
            group_cols = width_map[col_width]
            
            try:
                next_width = sorted_widths[i + 1]
            except IndexError:
                next_width = None
                diff = 0
                group_diff = reduction
            else:
                diff = abs(col_width - next_width)
                group_diff = diff * len(group_cols)
            
            if group_diff < reduction:
                # Reduce the widths of all columns in the group to match the
                # width of the next-widest column
                col_reduction = diff
                remainder = 0
                reduction -= group_diff
                
                # Add these columns to the next group, as they will all have
                # the same width
                width_map[next_width].extend(group_cols)
            else:
                # What's left of the reduction amount cannot be divided evenly
                # amongst all columns in the group - spread it out as evenly
                # as possible
                col_reduction, remainder = divmod(reduction, len(group_cols))
                reduction = 0
            
            if col_reduction:
                for col in group_cols:
                    col['render_width'] -= col_reduction
            
            if remainder:
                # Sort the list of columns by descending position, so the
                # remainder comes off later columns before earlier ones
                sorted_cols = sorted(group_cols, key=lambda c: c['pos'], reverse=True)
                for col in sorted_cols[:remainder]:
                    col['render_width'] -= 1
            
            if not reduction:
                break
    
    def set_title(self, title, alignment='centre'):
        
        self.title = RowWrapper(title, alignment)
    
    def set_footer(self, footer, alignment='right'):
        
        self.footer = RowWrapper(footer, alignment)
    
    def add_headings(self, headings):
        
        cols = self._columns
        
        if not cols:
            self._columns = [self._update_col_metadata({}, heading=h) for h in headings]
        elif len(cols) != len(headings):
            raise Exception('Number of headings does not match previously given number of columns.')
        else:
            for i, heading in enumerate(headings):
                self._update_col_metadata(cols[i], heading=heading)
        
        self._headings = headings
    
    def add_row(self, row):
        
        if row is self.BR or row is self.HR:
            self._rows.append(row)
            return
        
        if self._columns and len(self._columns) != len(row):
            raise Exception('Number of columns in row does not match previously given rows.')
        
        for i, value in enumerate(row):
            try:
                col_data = self._columns[i]
            except IndexError:
                self._columns.append({})
                col_data = self._columns[i]
            
            self._update_col_metadata(col_data, value=value)
        
        self._rows.append(row)
    
    def add_full_width_row(self, value, alignment='left'):
        
        row = RowWrapper(value, alignment)
        
        self._rows.append(row)
    
    def add_rows(self, rows):
        
        for row in rows:
            self.add_row(row)
    
    def get_rows(self):
        
        rows = [self.HR]
        
        if self._headings:
            rows.append(self._headings)
            rows.append(self.HR)
        
        rows.extend(self._rows)
        rows.append(self.HR)
        
        return rows
    
    def get_max_widths(self):
        
        outer_max_width = self._raw_max_width
        
        if outer_max_width is self.FULL_WIDTH:
            term_columns, term_rows = shutil.get_terminal_size()
            outer_max_width = int(term_columns)
        
        # The max width of actual data in the table is the outer max less the
        # space required for formatting the table itself
        
        # +4 for the "| " and " |" at the start and end of the line, and +3 for
        # the " | " spacer between each column
        formatting_buffer = 4 + ((len(self._columns) - 1) * 3)
        
        max_width = outer_max_width - formatting_buffer
        
        return outer_max_width, max_width
    
    def calculate_render_widths(self):
        
        total_width = 0
        min_width = 0
        width_map = {}
        
        # Determine full render widths per column as the max of the raw data
        # width and the heading width
        for i, col in enumerate(self._columns):
            col['pos'] = i
            col_width = max(col.get('raw_width', 0), len(col.get('heading', '')))
            col['render_width'] = col_width
            total_width += col_width
            min_width += min(col_width, self.MIN_COLUMN_WIDTH)
            
            # Map column widths to the columns with that width
            try:
                width_map[col_width].append(col)
            except KeyError:
                width_map[col_width] = [col]
        
        outer_max_width, max_width = self.get_max_widths()
        
        if max_width < min_width:
            raise Exception('Minimum table width exceeds maximum: table cannot be drawn.')
        
        # Get the amount by which the total table width needs to be reduced to
        # fit within the max width
        reduction = total_width - max_width
        
        if reduction <= 0:
            # No reduction of widths necessary
            return total_width
        
        total_width -= reduction
        
        self._reduce_column_widths(reduction, width_map)
        
        return total_width
    
    def build_table(self):
        
        formatting_buffer = 4 + ((len(self._columns) - 1) * 3)
        
        total_raw_width = self.calculate_render_widths()
        table_width = total_raw_width + formatting_buffer
        
        br = '|{0}|'.format(' ' * (table_width - 2))
        hr = '+{0}+'.format('-' * (table_width - 2))
        
        output = []
        
        if self.title:
            output.append(hr)
            output.extend(self.title.get_rows(table_width))
        
        for row in self.get_rows():
            if row is self.BR:
                output.append(br)
            elif row is self.HR:
                output.append(hr)
            elif isinstance(row, RowWrapper):
                output.extend(row.get_rows(table_width))
            else:
                row_str = []
                for i, col in enumerate(self._columns):
                    value = force_text(row[i]).replace('\n', '\\n').replace('\r', '\\r')
                    width = col['render_width']
                    
                    if len(value) > width:
                        value = '{0}...'.format(value[:width - 3])
                    
                    row_str.append(value.ljust(width))
                
                output.append('| {0} |'.format(' | '.join(row_str)))
        
        if self.footer:
            output.extend(self.footer.get_rows(table_width))
            output.append(hr)
        
        return '\n'.join(output)
