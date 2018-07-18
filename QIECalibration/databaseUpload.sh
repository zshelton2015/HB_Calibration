#!/usr/bin/env bash

# Rsync submission directory
rsync -a -e "ssh hep@cmshcal11" $1/Submission/* :/home/django/testing_database_hb/cal_uploader/temp/

# Run upload script
ssh hep@cmshcal11 'bash -s /home/django/testing_database_hb/cal_uploader/cal_upload.sh'
