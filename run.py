#!/Users/Kevin/Devel/python/.virtualenvs/infinote/bin/python
from app import infinote

application = infinote

if __name__ == "__main__":
  infinote.run(debug=True, host=infinote.config['HOST'], port=infinote.config['PORT'])
