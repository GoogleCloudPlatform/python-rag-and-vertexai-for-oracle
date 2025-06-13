/*
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

CREATE TABLE ElectricVehicles (
    VIN VARCHAR(50),
    COUNTY VARCHAR(50),
    CITY VARCHAR(50),
    STATE VARCHAR(50),
    POSTALCODE VARCHAR(20),
    MODELYEAR VARCHAR(10),
    MAKE VARCHAR(50),
    MODEL VARCHAR(50),
    ELECTRICVEHICLETYPE VARCHAR(50),
    CAFVELIGIBILITY VARCHAR(60),
    ELECTRICRANGE VARCHAR(50),
    BASEMSRP VARCHAR(50),
    LEGISLATIVEDISTRICT VARCHAR(50),
    DOLVEHICLEID VARCHAR(50),
    VEHICLELOCATION VARCHAR(50),
    ELECTRICUTILITY VARCHAR(100),
    CENSUSTRACT VARCHAR(50),
    ID NUMBER NOT NULL
);
