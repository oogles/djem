from django.contrib import messages

def parse_config(config):
    
    try:
        model = config['model']
        arg_name = config['arg_name']
        redir = None # base redirect
        
        ## TODO: Add Support for custom redirects
        #redir = config.get('redir', None)
    except TypeError:
        # Using "compact" config
        model, arg_name = config
        redir = None # base redirect
    
    return model, arg_name, redir

def model_exists(request, model, arg_name, kwargs):
    
    try:
        instance = model.objects.get(pk=kwargs[arg_name])
    except KeyError:
        # Argument optional
        return {}
    except model.DoesNotExist:
        # Invalid id given
        error = '{0} does not exist'.format(model._meta.verbose_name)
        messages.error(request, error)
        return None # trigger default redirect
    else:
        return {arg_name: instance}
