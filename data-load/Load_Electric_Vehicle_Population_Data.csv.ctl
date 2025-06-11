OPTIONS
(
ROWS=1000,
BINDSIZE=1048576
)
load data
infile 'Electric_Vehicle_Population_Data.csv'
into table ElectricVehicles
fields terminated by "," optionally enclosed by '"'
( VIN,
County,
City ,
State ,
PostalCode ,
ModelYear ,
Make ,
Model ,
ElectricVehicleType ,
CAFVEligibility,
ElectricRange ,
BaseMSRP ,
LegislativeDistrict ,
DOLVehicleID ,
VehicleLocation ,
ElectricUtility "SUBSTR(:ElectricUtility, 1, 100)",
CensusTract
 )
