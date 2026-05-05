# Clip Acquisition Director - Source-Commentary Pipeline

## 1. Stage Purpose
Perform just-in-time (JIT) download and extraction of approved evidence segments.

## 2. Inputs
- `clip_use_receipts` (Only those where `status == 'approved'`)

## 3. Outputs
- `extracted_clip_manifest`

## 4. Allowed Tools
- `video_downloader` (targeted range download)
- `video_trimmer`

## 5. Forbidden Actions
- **BLIND DOWNLOADS.** Only ranges specified in approved receipts may be downloaded.
- Accessing sources that do not have an approved receipt.

## 6. Required Checks
- Verify `in_seconds` and `out_seconds` match the downloaded segment.
- Check file existence after extraction.
- Record local file paths for the QC stage.

## 7. Failure Conditions
- Downloading a full source file when a range was requested.
- Missing clips from the extraction list.

## 8. Handoff Artifact Requirements
- List of `receipt_id` -> `local_path` mappings.
