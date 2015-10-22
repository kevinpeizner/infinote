#!/Users/Kevin/Devel/python/.virtualenvs/infinote/bin/python
from app import infinote
infinote.run(debug=True, host=infinote.config['HOST'], port=infinote.config['PORT'])
