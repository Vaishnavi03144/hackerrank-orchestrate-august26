import os
import pandas as pd

def load_data_and_context(dataset_dir="dataset"):
    messages_path = os.path.join(dataset_dir, "messages.csv")
    test_path = os.path.join(dataset_dir, "test.csv")
    
    if os.path.exists(test_path):
        messages_df = pd.read_csv(test_path)
    else:
        messages_df = pd.read_csv(messages_path)
        
    users_df = pd.read_csv(os.path.join(dataset_dir, "users.csv")) if os.path.exists(os.path.join(dataset_dir, "users.csv")) else None
    
    images_path = os.path.join(dataset_dir, "images.csv")
    images_df = pd.read_csv(images_path) if os.path.exists(images_path) else None

    vn_path = os.path.join(dataset_dir, "voice_notes.csv")
    vn_df = pd.read_csv(vn_path) if os.path.exists(vn_path) else None

    # Merge images if keys exist
    if images_df is not None:
        img_key = 'media_id' if 'media_id' in images_df.columns else ('image_id' if 'image_id' in images_df.columns else None)
        msg_key = 'media_id' if 'media_id' in messages_df.columns else ('message_id' if 'message_id' in messages_df.columns else None)
        if img_key and msg_key:
            messages_df = messages_df.merge(images_df, left_on=msg_key, right_on=img_key, how='left', suffixes=('', '_img'))

    # Merge voice notes if keys exist
    if vn_df is not None:
        vn_key = 'media_id' if 'media_id' in vn_df.columns else ('voice_note_id' if 'voice_note_id' in vn_df.columns else None)
        msg_key = 'media_id' if 'media_id' in messages_df.columns else ('message_id' if 'message_id' in messages_df.columns else None)
        if vn_key and msg_key:
            messages_df = messages_df.merge(vn_df, left_on=msg_key, right_on=vn_key, how='left', suffixes=('', '_vn'))

    return messages_df, users_df