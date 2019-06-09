#include "pch.h"
#include "WTC.h"
#include <fstream>
#include <iostream>
#include <ctime>




#pragma warning(disable : 4996)




WTC_telemetry myTelem;

const int numKeys = 8;
std::string basicKeys[numKeys] = { "IAS km/h",				// airspeed			km/h
									"type",					// acft type		type
									"altitude_hour",		// altitude			meters
									"flaps %",				// flap position	%
									"gear %",				// gear position	%
									"compass",				// heading			degrees
									"aviahorizon_pitch",	// pitch angle		degrees
									"aviahorizon_roll" };	// roll angle		degrees




void datalog(std::string csvName, dict basic);
std::string initializeCSV();
void writeHeaderToCSV(std::string csvName);
void writeToCSV(std::string csvName, std::string s);
void writeCommaToCSV(std::string csvName);
void writeNewlineToCSV(std::string csvName);




int main()
{
	dict indicators;
	dict state;
	dict combined;
	dict basic;

	myTelem.begin();

	std::string csvName = initializeCSV();
	writeHeaderToCSV(csvName);

	while (1)
	{
		indicators = myTelem.getIndicators();
		state = myTelem.getState();
		basic = myTelem.getBasic(indicators, state);

		datalog(csvName, basic);
		print(basic);
		print();
	}

	return 0;
}




void datalog(std::string csvName, dict map)
{
	dict::iterator it;

	writeToCSV(csvName, "0");
	writeCommaToCSV(csvName);
	
	for (int i = 0; i < numKeys; i++)
	{
		it = map.find(basicKeys[i]);

		if (it != map.end())
			writeToCSV(csvName, it->second);

		writeCommaToCSV(csvName);
	}

	writeToCSV(csvName, "-");
	writeNewlineToCSV(csvName);
}




std::string initializeCSV()
{
	time_t rawtime;
	struct tm * timeinfo;
	char buffer[80];

	time(&rawtime);
	timeinfo = localtime(&rawtime);

	strftime(buffer, sizeof(buffer), "%d-%m-%Y %H:%M:%S", timeinfo);
	std::string str(buffer);

	std::string csvName;

	csvName = "datalog_" + str + ".csv";
	csvName = replaceAll(csvName, '-', '_');
	csvName = replaceAll(csvName, ' ', '_');
	csvName = replaceAll(csvName, ':', '_');

	std::ofstream outFile;
	outFile.open(csvName, std::ios::out | std::ios::app);
	outFile.close();

	return csvName;
}




void writeHeaderToCSV(std::string csvName)
{
	writeToCSV(csvName, "sampleTime");
	writeCommaToCSV(csvName);

	for (int i = 0; i < numKeys; i++)
	{
		writeToCSV(csvName, basicKeys[i]);
		writeCommaToCSV(csvName);
	}

	writeToCSV(csvName, "comments");
	writeNewlineToCSV(csvName);
}




void writeToCSV(std::string csvName, std::string s)
{
	std::ofstream outFile;
	outFile.open(csvName, std::ios::out | std::ios::app);

	for (auto it = s.begin(); it != s.end(); it++)
		if ((*it != '\n') && (*it != ','))
			outFile << *it;

	outFile.close();
}




void writeCommaToCSV(std::string csvName)
{
	std::ofstream outFile;
	outFile.open(csvName, std::ios::out | std::ios::app);

	outFile << ',';

	outFile.close();
}




void writeNewlineToCSV(std::string csvName)
{
	std::ofstream outFile;
	outFile.open(csvName, std::ios::out | std::ios::app);

	outFile << '\n';

	outFile.close();
}