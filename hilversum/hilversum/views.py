'''
Created on Oct 25, 2017

@author: theo
'''
from leiden.views import HomeView as LeidenHome
import json

class HomeView(LeidenHome):
    template_name = 'hilversum/home.html'
    def get_context_data(self, **kwargs):
        context = LeidenHome.get_context_data(self, **kwargs)
        options = {
            'center': [52.22486,5.17463],
            'zoom': 13 }
        context['options'] = json.dumps(options)
        return context
