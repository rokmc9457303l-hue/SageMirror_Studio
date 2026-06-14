import json
import urllib.request
import time

print('Waiting for Streamlit to be available...')
time.sleep(2)
# Oh wait, we can't easily fetch rendered DOM via urllib because Streamlit is a React app. 
# We NEED a browser.
