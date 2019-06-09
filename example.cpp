#include "pch.h"
#include "WTC.h"




WTC_telemetry myTelem;




int main()
{
	dict indicators;
	dict state;
	dict combined;
	dict basic;

	myTelem.begin();

	while (1)
	{
		indicators = myTelem.getIndicators();
		state = myTelem.getState();
		basic = myTelem.getBasic(indicators, state);

		print(indicators);
		print();
		print(state);
		print();
		print(basic);
		print();
		print();
	}

	return 0;
}