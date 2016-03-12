MEASURE Parser 
===================

MEASURE is a language for expressing monitoring intents for NF-FGs, developed in the FP7 UNIFY project. 
This Python module is able to parse string containing MEASURE into dictionaries, JSON, YAML, or XML. 

Dependencies
-------------------
* Python3  
* PyParsing (pip3 install pyparsing)
* YAML and/or JSON libraries if this output is wanted

Install
------------------

```
$ python3 setup.py install
```

Use
-------------

```
from measure import MeasureParser
MeasureString = """ measurements { 
  m1 = delay.twoway.icmp.us.mean(source.ipv4 = 1.2.3.4, destination.ipv4 = 4.3.2.1, count = 100, freq = 0.4); 
  m2 = overload.risk.rx(interface = eth0);
}
zones { 
 z1 = ((AVG(val = m1, max_age = \"1 minute\") + 10.0) < 10);
 z2 = (AVG(val = m2, max_age = \"5 minute\") < 0.05);
 z3 = (AVG(val = m1, max_age = \"5 minute\") > 10.0);
}
actions { 
 z1 = Notify(target = \"controller\", message = \"we are in z1\"); Publish(topic = \"alarms\", message = \"warning\");
 z2 = Notify(target = \"controller\", message = \"we are in z2\");
 z3 = Notify(target = \"controller\", message = \"we are in z3\");
 z1->z3 = Notify(target = \"controller\", message = \"we are in z3\");
}"""
parser = MEASUREParser()
result = parser.parseToDict(MeasureString)
from pprint import pprint
pprint(result)
```

> **Contact:** ponsko@acreo.se
