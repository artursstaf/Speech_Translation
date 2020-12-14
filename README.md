# Speech Translation

## Instalation
Clone the repository and create conda environment by running `conda env create -f environment.yml`.

### Synthetic Data Filtering
Filter noise from synthetic speech translation dataset - (source, source_asr, source_pos, target). Source and Source_asr pairs that are not similar are dropped.

`python speech_translation.py filter --workdir= --source= --source_asr= --target= --source_pos= --target=
--result_source= --result_source_asr --result_target --result_source_pos`

### Rule-Based Synthetic Noise Generation
Learn suffix noise model from filtered synthetic dataset.

`python speech_translation.py learn_noise_model --workdir=workdir --source= --source_pos= --source_asr= --result_model=`

Apply suffix noise model to any parallel dataset.

`python speech_translation.py apply_noise_model --source= --source_pos= --target= --result_source= --result_target= --noise_model=`

Model ASR word split/merges.

`python speech_translation.py generate_split_merge --source= --target= --result_target= --result_source=`
