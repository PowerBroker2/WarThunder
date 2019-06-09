#pragma once
#include <fstream>
#include <iostream>
#include <urlmon.h>
#include <string>
#include <map>
#include <wininet.h>




typedef std::map<std::string, std::string> dict;




template<typename T> void print(T value);
void print(dict map);
void print();




class WTC_telemetry
{
public:
	void begin();
	dict getIndicators();
	dict getState();
	dict getBasic(dict indicators, dict state);
	dict getWebContents(char webAddress[]);

private:
	void htmlToString(char htmlFileName[], char htmlContentsBuff[], int buffLen);
	dict stringToMap(std::string const& s);
	std::string replaceAll(std::string const& s, char const c);
};
