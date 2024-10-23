"""Script to create Nemo compatible data manifests for jeli-asr"""

## Imports
import glob
import os
import csv
import random
import json
import shutil
import sys
from pydub import AudioSegment

# Key callable to sort wav files paths
def key_sort_paths(path: str) -> int:
    """Serve as key function to sort the wav files paths

    Args:
        path (str): An individual path

    Returns:
        int: The number of the split (between 1 and 6)
    """
    return int(path[-5])

# Function to read and combine the audios
def read_audios(glob_paths: list[str]) -> AudioSegment:
    """Read the six 10 mns audio as AudioSegments and returns the combined 1 hr audio

    Args:
        glob_paths (list[str]): list of the paths of the 6 .wav files

    Returns:
        AudioSegment: The combined audio
    """
    audios = []
    for wav_file in sorted(glob_paths, key=key_sort_paths):
        audios.append(AudioSegment.from_file(file=wav_file, format="wav"))
    final_audio = sum(audios[1:], start=audios[0])
    return final_audio

# A function that reads and return the utterances from .tsv files
def read_tsv(tsv_file_path: str) -> list[list[int | str]]:
    """Read a .tsv file and return the utterances in it

    Args:
        tsv_file_path (str): The path to the tsv file

    Returns:
        list[list[int | str]]: The returned utterances with the timestamps coverted to int
    """
    with open(tsv_file_path,"r", encoding='utf-8') as recording_transcript:
        tsv_file_rows = csv.reader(recording_transcript, delimiter="\t")
        utterances = [[int(start), int(end), bam, french] for start, end, bam, french in tsv_file_rows]
    return utterances
            
# Function to subdivide the audio (transcript) into multiple variable length slices
def create_var_length_samples(utterances: list[list[int | str]], min_duration: int = 1000,
                max_duration: int = 120000) -> list[list[list[int | str]]]:
    """Create variable length combination of utterances to make samples which duration vary between 1s and 2mns

    Args:
        utterances (list[list[int  |  str]]): The read tsv file containing the transcriptions of the audio
        min_duration (int, optional): min duration of a sample in milliseconds. Defaults to 1000.
        max_duration (int, optional): max duration of a sample in milliseconds. Defaults to 120000.

    Returns:
        list[list[list[int | str]]]: The list of created samples
    """
    samples = []
    current_slice = []
    current_duration = 0

    i = 0
    while i < len(utterances):
        utterance_start, utterance_end = utterances[i][:2]
        utterance_duration = utterance_end - utterance_start
        
        # If current slice duration is less than max duration, add the utterance to this sample
        if current_duration + utterance_duration <= max_duration:
            current_slice.append(utterances[i])
            current_duration += utterance_duration
            i += 1
        else:
            # Save the current sample and reset for a new one
            samples.append(current_slice)
            current_slice = []
            current_duration = 0
        
        # Randomly decide whether to end the current sample based on time or number of utterances
        if current_duration >= min_duration:
            if random.choice([True, False, False]) or len(current_slice) >= random.randint(1, 20):
                samples.append(current_slice)
                current_slice = []
                current_duration = 0

    # Add the final slice if it exists
    if current_slice: # equivalent to if current_slice is empty
        samples.append(current_slice)

    return samples

# Function to create and save the audio samples for a specific list of samples
def slice_and_save_audios(samples: list[list[list[int | str]]], griot_id: str,
                          data_dir: str, audio_dir_path: str) -> list[list[float | str]]:
    """Slice and save the audio samples created for a specific 1hr recording

    Args:
        samples (list[list[list[int  |  str]]]): The samples created with function "create_var_length_samples"
        griot_id (str): The ID of the griot in the recording (eg: griots_r17)
        data_dir (str): The directory containing all the data.
        audio_dir_path (str): The diretory the save the sliced audios in.

    Returns:
        list[list[int | str]]: A list version of manifests (eg: [[audiofile_path, duration, bambara, translation], ...])
    """
    wav_files_paths = glob.glob(f'{data_dir}/{griot_id}/*.wav')
    griot_recording = read_audios(glob_paths=wav_files_paths)
    # A list to store only the data needed to create 
    list_manifests = []

    for sample in samples:
        start = sample[0][0]
        end = sample[-1][1]
        duration = (end - start) / 1000 # in seconds
        # Flag audios with more than 100 seconds 
        more_than_100s = " ###" if duration >= 100 else ""

        # get trancriptions and translations of utterances composing the samples
        transcriptions, translations = [utt[2] for utt in sample], [utt[3] for utt in sample]
        transcription = " ".join(transcriptions)
        translation = " ".join(translations)

        # create the sample wav file and save it
        audio_file_path = f"{audio_dir_path}/{griot_id}-{start}-{end}.wav"
        griot_recording[start:end].export(out_f=audio_file_path, format="wav")
        print(f"Sample {griot_id}-{start}-{end} saved in {audio_file_path}{more_than_100s}")

        # Create the manifest list and save it
        list_manifests.append([audio_file_path, duration, transcription, translation])
    return list_manifests

# A function to shuffle and split samples
def shuffle_and_split(dataset: list[list[float | str]],
                      test: int | float = 0.15) -> tuple[list[list[float | str]]]:
    """Shuffle and split the whole dataset

    Args:
        dataset (list[list[int  |  str]]): The combined list of all list manifest returned by "slice_and_save_audios"
        test (int | float, optional): The number of sample to include that make the test set or and percentage of the whole dataset to use as the test set. Defaults to 0.15.

    Returns:
        tuple[list[list[list[int | str]]]]: The train and test sets samples returned separately
    """
    random.shuffle(dataset)
    if isinstance(test, float):
        test = int(test * len(dataset))
    test_set_samples = dataset[0:test]
    train_set_samples = dataset[test:]
    return train_set_samples, test_set_samples

# A function to create audio sample files and manifests
def create_manifest(dataset_split: list[list[float | str]], split_name: str,
                    dir_path: str) -> None:
    """Create manifest files 

    Args:
        dataset_split (list[list[float  |  str]]): Split of the dataset to create manifest for
        split_name (str): Name of the split
        dir_path (str): The directory to save the new data manifest in
    """
    # Ensure directories for manifests and audios
    os.makedirs(f'{dir_path}/manifests', exist_ok=True)
    os.makedirs(f'{dir_path}/french-manifests', exist_ok=True)
    os.makedirs(f'{dir_path}/audios/{split_name}', exist_ok=True)

    # Define manifest file paths
    manifest_path = f'{dir_path}/manifests/{split_name}_manifest.json'
    french_manifest_path = f'{dir_path}/french-manifests/{split_name}_french_manifest.json'
    audio_dir_path = f'{dir_path}/audios/{split_name}'

    with open(manifest_path, 'w', encoding="utf-8") as manifest_file, open(french_manifest_path, 'w', encoding="utf-8") as french_file:
        for sample in dataset_split:
            # move the audio sample file in the corresponding split directory
            new_audio_path = f'{audio_dir_path}/{sample[0].split("/")[-1]}'
            shutil.move(src=sample[0], dst=new_audio_path)

            # Prepare the manifest line
            manifest_line = {
                "audio_filepath": os.path.relpath(new_audio_path),
                "duration": sample[1],
                "text": sample[2]  # Bambara transcription goes to the text field
            }

            french_manifest_line = {
                "audio_filepath": os.path.relpath(new_audio_path),
                "duration": sample[1],
                "text": sample[3]
            }

            # Write manifest files
            manifest_file.write(json.dumps(manifest_line) + '\n')
            french_file.write(json.dumps(french_manifest_line) + '\n')
    print(f"{split_name} manifests files have been created successfully!\nCorresponding audios files have been moved to {audio_dir_path}")

if __name__ == "__main__":
    data_path = sys.argv[1]
    manifest_dir = sys.argv[2]
    tsv_dir = f'{data_path}/aligned-transcriptions'

    # Get all the revised transcription files in .tsv format
    tsv_paths = glob.glob(f'{tsv_dir}/*.tsv')
    # list to store the list manifests per griots
    final_list_manifest = []
    for tsv_file in tsv_paths:
        id_griot = tsv_file.split("/")[-1][:-4]
        griot_utterances = read_tsv(tsv_file_path=tsv_file)
        # Get samples (can be made of one or more utterances)
        griot_samples = create_var_length_samples(utterances=griot_utterances)
        list_manifest = slice_and_save_audios(samples=griot_samples, griot_id=id_griot,
                                    data_dir=data_path, audio_dir_path=f'{manifest_dir}/audios')
        final_list_manifest.append(list_manifest)
    # Get a single list manifest for all the samples
    final_list_manifest = sum(final_list_manifest, start=[])
    # Shuffle and split the final list of all sample,manifests
    train_set, test_set = shuffle_and_split(dataset=final_list_manifest, test=0.15) # Use 15% of the dataset for test
    print(f'len(train_set) == {len(train_set)} and len(test_set) == {len(test_set)}')

    create_manifest(dataset_split=train_set, split_name="train", dir_path=manifest_dir)
    create_manifest(dataset_split=test_set, split_name="test", dir_path=manifest_dir)
