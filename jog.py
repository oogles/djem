from jogger.tasks import DocsTask, LintTask, TestTask
from jogger.tasks._release import ReleaseTask

tasks = {
    'docs': DocsTask,
    'lint': LintTask,
    'test': TestTask,
    'release': ReleaseTask
}
