from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from utkik.decorators import http_methods


class ViewException(Exception):
    pass


class ContextData(object):
    """This will contain attributes for context. All the attributes are later
    collected by ContextData().__dict__.
    """


class View(object):
    """A minimalist View base class.

    Goals
    -----
    - Building context for rendering should be simple.

    - Source should be easy to follow and encourage this for implementing
      subclasses if possible.

    - Keep methods short and provide useful hooks for sub classing.

    - Embrace the instance and don't pass request nor context around.

    - Narrow the scope to most common use but without limiting less usual
      use-cases.
    """

    methods = ['GET', 'POST'] # allowed HTTP methods
    decorators = [] # a list of decorators
    template = None # template to render to
    ajax_template = None # template to render to for ajax calls

    def __init__(self):
        """All we do here is to instantiate the ContextData class"""
        self.c = ContextData() # c is for context
        self.request = None

    def dispatch(self, request, *args, **kwargs):
        """View entry point. The utkik dispatcher will create a new instance of
        the current class and call this method when the Django handler makes a
        call to the view.
        """
        self.request = request
        return self._decorate(self.get_response)(request, *args, **kwargs)

    def _decorate(self, f):
        """Decorate function f with decorators from ``self.decorators`` and
        decorators based on ``self.methods``.
        """
        for d in reversed(self.decorators):
            f = d(f)
        methods = [m for m in self.methods if hasattr(self, m.lower())]
        return http_methods(*methods)(f)

    def get_response(self, request, *args, **kwargs):
        """Returns the response from a successful request to the view. In it's
        default implementation it will direct to a suitable handler method based
        on the HTTP method call. If this handler does not return a response, we
        will simply call and return ``self.render``. Request is just passed in
        here for decorator compatibilty reasons.
        """
        return self.get_handler()(*args, **kwargs) or self.render()

    def get_handler(self):
        """Return a suitable handler. You can override this for example if you
        want another handler for ajax calls.
        """
        return getattr(self, self.request.method.lower())

    def get_context(self):
        """If you want to add some extra context or modify the current context
        this is a good place. This method is called from ``self.render``.
        """
        return self.c.__dict__

    def get_template(self):
        """Returns a template for ``self.render`` method, this is mostly for
        having an alternative template for ajax calls.
        """
        if self.request.is_ajax() and self.ajax_template:
            return self.ajax_template
        if not self.template:
            raise ViewException(
                _('%s does not define a template to render to.') % self)
        return self.template

    def render(self):
        """
        Renders ``self.get_context()`` to ``self.template``. This is called from
        ``self.get_response`` if the handler does not return a response.
        """
        return render_to_response(self.get_template(), self.get_context(),
            RequestContext(self.request))

