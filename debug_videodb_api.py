
import inspect
import videodb
from videodb import timeline

print("VideoDB Dir:", dir(videodb))

if hasattr(videodb, 'Video'):
    print("\nVideo Class:")
    print(dir(videodb.Video))
    print(inspect.signature(videodb.Video.__init__))

print("\nTimeline.generate_stream Full source:")
try:
    print(inspect.getsource(timeline.Timeline.generate_stream))
except:
    print("Could not get source")

print("\nDefault Timeline __init__:")
print(inspect.signature(timeline.Timeline.__init__))
