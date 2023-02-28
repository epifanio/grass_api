
# methods to perform some processing
# the worker can be used on the main machine
# or we can, later on. send them to celery + rabbitmq

def create_location(config_dict):
    response = parse_spec(config_dict)
    return response


def parse_spec(config_dict):
    return False
