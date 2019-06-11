#include "pch.h"
#include "WTC.h"
#include <fstream>
#include <iostream>
#include <urlmon.h>
#include <string>
#include <map>
#include <wininet.h>




void WTC_telemetry::begin()
{
	return;
}




dict WTC_telemetry::getIndicators()
{
	char webAddress[] = "http://localhost:8111/indicators";
	return getWebContents(webAddress);
}




dict WTC_telemetry::getState()
{
	char webAddress[] = "http://localhost:8111/state";
	return getWebContents(webAddress);
}




dict WTC_telemetry::getBasic(dict indicators, dict state)
{
	const int numKeys = 8;
	std::string basicKeys[numKeys] = {	"IAS km/h",		// airspeed		km/h
						"type",			// acft type		type
						"altitude_hour",	// altitude		meters
						"flaps %",		// flap position	%
						"gear %",		// gear position	%
						"compass",		// heading		degrees
						"aviahorizon_pitch",	// pitch angle		degrees
						"aviahorizon_roll" };	// roll angle		degrees
	dict::iterator it;
	dict results_map;

	for (int i = 0; i < numKeys; i++)
	{
		it = indicators.find(basicKeys[i]);
		if (it != indicators.end())
			results_map.emplace(it->first, it->second);
		else
		{
			it = state.find(basicKeys[i]);
			if (it != state.end())
				results_map.emplace(it->first, it->second);
			else
				print("key " + basicKeys[i] + " not found");
		}
	}

	return results_map;
}




dict WTC_telemetry::getWebContents(char webAddress[])
{
	const int buffLen = 2048;
	char htmlFileName[] = "result.html";
	char htmlContentsBuff[buffLen] = { ' ' };

	dict results_map;

	HRESULT hr = URLDownloadToFile(NULL, webAddress, htmlFileName, 0, NULL);
	if (hr == S_OK)
	{
		htmlToString(htmlFileName, htmlContentsBuff, buffLen);
		results_map = stringToMap(htmlContentsBuff);
	}
	else
		results_map.emplace("error", "WT not running");

	DeleteUrlCacheEntry(webAddress);
	remove(htmlFileName);

	return results_map;
}




void WTC_telemetry::htmlToString(char htmlFileName[], char htmlContentsBuff[], int buffLen)
{
	std::ifstream fin(htmlFileName);
	fin.read(htmlContentsBuff, 2048);
}




dict WTC_telemetry::stringToMap(std::string const& s)
{
	dict m;

	std::string::size_type key_pos = 0;
	std::string::size_type key_end;
	std::string::size_type val_pos;
	std::string::size_type val_end;

	std::string fString = "";
	fString = removeAll(s, '\"');
	fString = removeAll(fString, ',');
	fString = removeAll(fString, '{');
	fString = removeAll(fString, '}');

	while ((key_end = fString.find(':', key_pos)) != std::string::npos)
	{
		if ((val_pos = fString.find_first_not_of(": ", key_end)) == std::string::npos)
			break;

		val_end = fString.find('\n', val_pos);
		m.emplace(fString.substr(key_pos, key_end - key_pos), fString.substr(val_pos, val_end - val_pos));

		key_pos = val_end;
		if (key_pos != std::string::npos)
			++key_pos;
	}

	return m;
}




std::string removeAll(std::string const& s, char const c)
{
	std::string returnString = "";

	for (std::string::size_type i = 0; i != s.length(); i++)
		if (s[i] != c)
			returnString += s[i];

	return returnString;
}




std::string replaceAll(std::string const& s, char const c, char const r)
{
	std::string returnString = "";

	for (std::string::size_type i = 0; i != s.length(); i++)
		if (s[i] != c)
			returnString += s[i];
		else
			returnString += r;

	return returnString;
}




template<typename T>
void print(T value)
{
	std::cout << value << std::endl;
}




void print(dict map)
{
	for (auto it = map.begin(); it != map.end(); it++)
		std::cout << it->first << " => " << it->second << std::endl;
}




void print()
{
	std::cout << std::endl;
}
