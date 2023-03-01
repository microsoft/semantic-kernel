import os

def list_available_models():
    model_folders = os.listdir('./models')
    models = []
    for folder in model_folders:
        models.append(folder)
    return models

def is_model_available(model_name):
    model_folders = os.listdir('./models')
    for folder in model_folders:
        if model_name in folder:
            return folder
    return None

