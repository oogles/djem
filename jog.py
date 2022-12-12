from jogger.tasks import DocsTask, LintTask, TestTask
from jogger.tasks._release import ReleaseTask


def docker_down(settings, stdout, stderr):
    """
    Stop and remove the Docker containers for local development.
    """
    
    answer = input('Destroy docker containers? [Y/n] ')
    
    if answer.lower() != 'y':
        return
    
    return 'docker compose down --remove-orphans'


tasks = {
    'release': ReleaseTask,
    
    # Docker tasks. Run on the host to control Docker.
    'up': 'docker compose up --wait',
    'stop': 'docker compose stop',
    'down': docker_down,
    'ssh': 'docker exec -it djem /bin/bash',
    
    # Dev tasks. Run on the guest to aid development.
    'docs': DocsTask,
    'lint': LintTask,
    'test': TestTask
}
