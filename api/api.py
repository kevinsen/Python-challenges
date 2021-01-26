import asyncio
import os
import re
from functools import wraps

import connexion
import uvloop
import yaml
from aiohttp import web

API_CONFIG_FILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'api_conf.yaml')
API_SPEC_DIR_PATH = os.path.abspath(os.path.dirname(__file__))

# API Controllers

async def read_file_controller(request, path=None):
    """API controller to read a file given its relative path.

    Parameters
    ----------
    request : connexion.request
    path : str, opt
        Relative path to a file. Default `None`

    Returns
    -------
    Content of the file.
    """
    try:
        data = await framework_read_file(path=path)
        return web.json_response(data=data, status=200)
    except re.error as e:
        return web.json_response(data={'error': e.msg}, status=400)


# Framework

def data_path_validator():
    """Decorator to handle exceptions.

    Raises
    ------
    re.error

    Returns
    -------
    Function result.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            validator = re.compile('^data/[\w\-./]+$')
            if re.match(validator, kwargs['path']):
                return func(*args, **kwargs)
            else:
                raise re.error('Invalid path')
        return wrapper
    return decorator


@data_path_validator()
async def framework_read_file(path :str = ''):
    """Read a file given its relative path.

    Parameters
    ----------
    path : str
        Relative path to a file.
    Returns
    -------
    Content of the file.
    """
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), path)) as f:
        return f.read()


def basic_login(username, password, required_scopes=None):
    """Convenience method to use in OpenAPI specification.

    Parameters
    ----------
    username : str
        Unique username.
    password : str
        User password.
    required_scopes

    Returns
    -------
    Dictionary with the username and his status if the the credentials are correct. `None` otherwise.
    """
    return {'sub': username, 'active': True } if username == 'wazuh' and password == 'test' else None


def read_yaml_config(config_file=API_CONFIG_FILE_PATH):
    """Read a YAML file.

    Parameters
    ----------
    config_file : str, optional
        Absolute path to the API configuration file. Default `API_CONFIG_FILE_PATH`

    Returns
    -------
    Content of the YAML file.
    """
    with open(config_file) as f:
        return yaml.load(f)


def start():
    # Set up API
    api_conf = read_yaml_config()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    app = connexion.AioHttpApp(__name__, host=api_conf['host'],
                               port=api_conf['port'],
                               specification_dir=API_SPEC_DIR_PATH,
                               options={"swagger_ui": False},
                               only_one_api=True
                               )

    # Add API
    app.add_api('api_spec.yaml',
                arguments={'title': 'Test API',
                           'protocol': 'http',
                           'host': api_conf['host'],
                           'port': api_conf['port']
                           },
                strict_validation=True,
                validate_responses=False,
                pass_context_arg_name='request')

    # Start API
    app.run(port=api_conf['port'],
            host=api_conf['host'],
            use_default_access_log=True
            )

# Main loop
if __name__ == '__main__':
    start()
