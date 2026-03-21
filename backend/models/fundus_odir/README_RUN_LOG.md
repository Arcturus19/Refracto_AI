# Fundus (ODIR-5K) Training Run Log

This file is intentionally kept as a *live* log of actions taken to train the Fundus model.

## Log

- 2026-03-21: Added [backend/services/ml_service/train_fundus_odir.py](backend/services/ml_service/train_fundus_odir.py) to train ODIR-5K fundus multi-label model directly from [backend/data/Fundus/archive.zip](backend/data/Fundus/archive.zip) without extraction.
- 2026-03-21: Confirmed zip contains `full_df.csv` (6392 rows) and images under `ODIR-5K/ODIR-5K/... Images/`.
- 2026-03-21: GPU check: CUDA not available (`cuda_available=False`). Training will run on CPU.
- 2026-03-21: Dry-run command (OK):
	- `python train_fundus_odir.py --zip-path backend/data/Fundus/archive.zip --model efficientnet_b0 --img-size 224 --batch-size 8 --workers 0 --dry-run --model-dir backend/models/fundus_odir`
	- Observed split sizes: train=5114, val=639, test=639
- 2026-03-21: Started full training (background terminal) and manually stopped during Epoch 1 (~67% of training batches). No checkpoints were written yet because this script saves checkpoints at the end of each epoch.
- 2026-03-21: Verified checkpoints exist and represent a completed run to epoch 10:
	- `backend/models/fundus_odir/fundus_odir_last.pt` (checkpoint `epoch=10`)
	- `backend/models/fundus_odir/fundus_odir_best.pt`
	- Note: the current `backend/models/fundus_odir/training_log.json` was written by an eval-only run (no new epochs executed) because `--epochs` matched the checkpoint epoch.
