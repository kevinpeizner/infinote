import pafy
import re
import os.path
import threading



####################
### Text Parsing ###
####################
def parsechannel(text):
    t = re.sub('vevo$', '', text, flags=re.I) # Remove trailing 'vevo'
    t = re.sub('tv$', '', t, flags=re.I) # Dido for 'tv'
    if not re.search('^UKF', t):
        t = ' '.join(re.findall('[A-Z][^A-Z\\s]*', t)) # Break up on camel case
    return t

def parsetitle(text):
    # Look for these words within brackets/parenthesis. 
    bracket_keywords=('monstercat', 'release', 'official', 'music', 'video', 'audio')

    splits = re.split(r'-', text)
    for i in range(len(splits)):
        splits[i] = re.sub('^\[.*\]\s*', '', splits[i]) # Remove anything in brackets at the very beginning.
        # Remove keywords and their surrounding brackets/parenthesis.
        splits[i] = re.sub('\s{0,1}[\[\(].*['+'|'.join(bracket_keywords)+'].*[\]\)]', '', splits[i], flags=re.I)
        splits[i] = re.sub('^\s+', '', splits[i]) # Remove spaces at the beginnig.
        splits[i] = re.sub('\s+$', '', splits[i]) # Remove spaces at the end.

    splits = filter(None, splits) # Filter out empty strings
    clean_string = ' - '.join(splits) # Join together new string
    return clean_string



###################
### Downloading ###
###################
def progress_cb(total, recvd, ratio, rate, eta):
    status_string = ('  {:,} Bytes [{:.2%}] received. Rate: [{:4.0f} '
                                 'KB/s].  ETA: [{:.0f} secs]')
    prg_stats = (recvd, ratio, rate, eta)
    status = status_string.format(*prg_stats)
    print(status)

def download(audio_stream, filepath, callback):
    print('START DOWNLOAD')
    audio_stream.download(filepath=filepath, quiet=True, callback=callback)
    print('FINISHED DOWNLOAD')

def getaudio(url, path=".", cb=progress_cb):
    if 'www.' in url and 'www.youtube.com/watch?v=' not in url:
      print('ERROR: Url does not point to youtube.')
      return 'ERROR: Url does not point to youtube.'

    # Can take 11 char video id or full link
    # Fails silently when using full url to non-youtube site
    try:
      video = pafy.new(url)
    except ValueError as err:
      # invalid v_id
      print(err.args)
      raise err
    except OSError as err:
      # invalid full youtube url
      print(err.args)
      raise err
    except Exception as err:
      # unknown error
      print(type(err))
      print(err.args)
      print(err)
      raise err

    # Generate file name & path.
    audio = video.getbestaudio()
    filename = parsetitle(video.title)
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        path='.'
    path +='/'+filename+'.'+audio.extension

    # Kick off actual downloading onto another thread.
    t = threading.Thread(target=download, args=(audio, path, cb))
    t.start()

    return filename



############
### Main ###
############
if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=3hlZQuAR7KI"
    getaudio(url)
    
    #### Test text ####
    #text="[Future Bass] - Grant Bowtie - High Tide [Monstercat Release]"
    #text2="Varien - Supercell (feat. Veela) [Monstercat Official Music Video]"
    #text3="Ellie Goulding - Love Me Like You Do (Official Video)"
    #text4="Taylor Swift - Bad Blood ft. Kendrick Lamar"
    #text5="Major Lazer & DJ Snake - Lean On (feat. MØ) (Official Music Video)"
    #text6="Wiz Khalifa - See You Again ft. Charlie Puth [Official Video] Furious 7 Soundtrack"
    #text7="Eminem - Kings Never Die (Audio) ft. Gwen Stefani"
    #text8="Macy Gray- B.O.B (Official Music Video)"
    #textarray=[text,text2,text3,text4,text5,text6,text7,text8]
    #
    #for i in range(len(textarray)):
    #    textarray[i] = parsetitle(textarray[i])
    #    print(textarray[i])
    #
    #### End Test ####
    
#    chnl1="UKF Dubstep"
#    chnl2="UKF Drum & Bass"
#    chnl3="UKF"
#    chnl4="Monstercat"
#    chnl5="MeekMillTV"
#    chnl6="TaylorSwiftVEVO"
#    chnl7="Iron Maiden"
#    chnl8="Ryan Lewis Test"
#    
#    chnl_array=(chnl1,chnl2,chnl3,chnl4,chnl5,chnl6,chnl7, chnl8)
#    folders = []
#    
#    for i in range(len(chnl_array)):
#        folders.append(parsechannel(chnl_array[i]))
#        print(folders[i])
