from videodb import timeline, asset
import inspect

print("--- Assets ---")
try:
    if hasattr(timeline, 'TextAsset'):
        print(f"TextAsset: {inspect.signature(timeline.TextAsset)}")
    elif hasattr(asset, 'TextAsset'):
        print(f"TextAsset: {inspect.signature(asset.TextAsset)}")
        
    if hasattr(timeline, 'AudioAsset'):
        print(f"AudioAsset: {inspect.signature(timeline.AudioAsset)}")
except Exception as e:
    print(e)
