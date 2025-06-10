# genai-db-samples

This code asssumes you have Oracle Database up and running and can login as user rw_user, ro_user for readonly.
Use sqlplus as rw_user to create-table-electric-vehicles.sql to create table
Download data from https://catalog.data.gov/dataset/electric-vehicle-population-data as .csv file
Import into Oracle database using Load_Electric_Vehicle_Population_Data.csv.ctl
sqlldr rw_user@localhost:1521/FREEPDB1 CONTROL=Load_Electric_Vehicle_Population_Data.csv.ctl


