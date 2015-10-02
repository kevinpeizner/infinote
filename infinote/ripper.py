import pafy
import re
import os.path

# Look for these words within brackets/parenthesis. 
bracket_keywords=('monstercat', 'release', 'official', 'music', 'video', 'audio')

def parsechannel(text):
    t = re.sub('vevo$', '', text, flags=re.I) # Remove trailing 'vevo'
    t = re.sub('tv$', '', t, flags=re.I) # Dido for 'tv'
    if not re.search('^UKF', t):
        t = ' '.join(re.findall('[A-Z][^A-Z\\s]*', t)) # Break up on camel case
    return t

def parsetitle(text):
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

status_string = ('  {:,} Bytes [{:.2%}] received. Rate: [{:4.0f} '
                                 'KB/s].  ETA: [{:.0f} secs]')

def progress_cb(total, recvd, ratio, rate, eta):
    prg_stats = (recvd, ratio, rate, eta)
    status = status_string.format(*prg_stats)
    print(status)

def getaudio(url, path):
    video = pafy.new(url)
#    print(video.username)
    filename = parsetitle(video.title)
    print(filename)
    audio = video.getbestaudio()

    path = os.path.abspath(path)
    if not os.path.isdir(path):
        path='.'
    path +='/'+filename+'.'+audio.extension

    print(path)

    audio.download(filepath=path, quiet=True, callback=progress_cb)
    return filename

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=3hlZQuAR7KI"
    getaudio(url, ".")
    
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
    
    chnl1="UKF Dubstep"
    chnl2="UKF Drum & Bass"
    chnl3="UKF"
    chnl4="Monstercat"
    chnl5="MeekMillTV"
    chnl6="TaylorSwiftVEVO"
    chnl7="Iron Maiden"
    chnl8="Ryan Lewis Test"
    
    chnl_array=(chnl1,chnl2,chnl3,chnl4,chnl5,chnl6,chnl7, chnl8)
    folders = []
    
    for i in range(len(chnl_array)):
        folders.append(parsechannel(chnl_array[i]))
        print(folders[i])
