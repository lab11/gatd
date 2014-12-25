from pyramid.view import view_config


@view_config(route_name='home', renderer='templates/home.jinja2')
def home(request):
    return {}
