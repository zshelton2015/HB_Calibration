#!/bin/bash
rsync uidlist.txt cmshcal11:/home/django/testing_database_hb/query/uidlist.txt
ssh -YCK cmshcal11 'cd /home/django/testing_database_hb/query ; python cardLookup.py uidlist.txt'
rsync cmshcal11:/home/django/testing_database_hb/query/mapping.json .
