import os
import shutil

# This script cleans up temporary Python files and trained model caches
def cleanup():
    folders_to_clear = ['__pycache__', 'models/__pycache__', 'services/__pycache__']
    for folder in folders_to_clear:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Cleared: {folder}")
    
    if os.path.exists('models/saved_model.pkl'):
        os.remove('models/saved_model.pkl')
        print("Removed trained model cache.")

if __name__ == "__main__":
    cleanup()