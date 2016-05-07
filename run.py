#!/usr/bin/env python
from app import infinote
from app.config import infinote_app

infinote_app.run(host=infinote_app.config['HOST'], port=infinote_app.config['PORT'], debug=True)
