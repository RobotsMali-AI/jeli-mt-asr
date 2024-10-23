# jeli-asr-data-manifest

This repository contains a resampled version of `jeli-asr` dataset with correponding NeMo data manifests.

## Directory Structure

The directory structure is as follows:

```
jeli-data-manifest/
│
├── audios/
│   ├── train/
│   └── test/
│
├── french-manifests/
│   ├── train_french_manifest.json
│   └── test_french_manifest.json
│
├── manifests/
│   ├── train_manifest.json
│   └── test_manifest.json
│
└── scripts/
    └── create_manifest.py
    └── clean_tsv.py
```

### 1. **audios/**
This directory contains the audio files (.wav format) of every example in the dataset. The audio files are split into two subdirectories:
- **train/**: Contains audio files used for training.
- **test/**: Contains audio files used for testing.

The audio files vary in length and correspond to each entry in the manifest files. They are referenced by file paths in the manifest files. The audios directory has not been uploaded to github but it is accessible on [google drive](#)

### 2. **manifests/**
This directory contains the manifest files used for training speech recognition (ASR) models. There are two JSON files:
- **train_manifest.json**: Contains file paths, durations, and transcriptions for the training set.
- **test_manifest.json**: Contains file paths, durations, and transcriptions for the test set.

Each line in the manifest files is a JSON object with the following structure:
```json
{
  "audio_filepath": "jeli-data-manifest/audios/train/griots_r19-1609461-1627744.wav",
  "duration": 18.283,
  "text": "I kun tɛ kɔrɔta maa min si kakɔrɔ n'ita ye, i ŋɛ t'a ŋɛ ye..."
}
```
- **audio_filepath**: The relative path to the corresponding audio file.
- **duration**: The duration of the audio file in seconds.
- **text**: The transcription of the audio in Bambara.

### 3. **french-manifests/**
This directory contains French equivalent manifest files for the dataset. The structure is similar to the `manifests/` directory but with French transcriptions:
- **train_french_manifest.json**: Contains the French transcriptions for the training set.
- **test_french_manifest.json**: Contains the French transcriptions for the test set.

### 4. **scripts/**
This directory contains scripts used to process the data and create manifest files:
- **create_manifest.py**: A script used to create manifest files for training and testing. It samples the audio files and generates the corresponding JSON manifest files.
- **clean_tsv.py**: Script to remove some of the most common issues in the .tsv transcription files, such as unwanted characters (", <>), consecutive tabs (making some rows incositent) and spacing errors

## Dataset Overview

The dataset consists of 11,582 audio-transcription pairs:
- **Training set**: 9,845 examples (85%)
- **Test set**: 1,737 examples (15%)

Each audio file is paired with a transcription in Bambara, and the corresponding French transcriptions are available in the `french-manifests/` directory.

## Usage

The manifest files are specifically created for training Automatic Speech Recognition (ASR) models in NVIDIA NeMo, but they can be used with any other framework that supports manifest-based input formats.

To use the dataset, simply load the manifest files (`train_manifest.json` and `test_manifest.json`) in your training script. The file paths for the audio files and the corresponding transcriptions are already provided in these manifest files.

### Example NeMo Usage

```python
from nemo.collections.asr.models import ASRModel
train_manifest = 'jeli-data-manifest/manifests/train_manifest.json'
test_manifest = 'jeli-data-manifest/manifests/test_manifest.json'

asr_model = ASRModel.from_pretrained("QuartzNet15x5Base-En")
asr_model.setup_training_data(train_data_config={'manifest_filepath': train_manifest})
asr_model.setup_validation_data(val_data_config={'manifest_filepath': test_manifest})
```

## Issues
This version has just performed some shallow cleaning on the transcriptions and resampled the audios. It has conserved most of the issues of the original dataset such as:

- **Misaligned / Invalid segmentation**
- **Language / Incorrect transcriptions**
- **Non-standardized naming conventions**

## Citation

If you use this dataset in your research or project, please give credit to the creators of the original Jeli-ASR dataset. 

---
