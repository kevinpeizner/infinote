#!/usr/bin/env python
from app import infinote
infinote.run(debug=True, host=infinote.config['HOST'], port=infinote.config['PORT'])
