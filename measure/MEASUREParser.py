#!/usr/bin/python3
# coding=utf(-8)
__author__ = 'eponsko'
from pyparsing import Combine,Regex,Word,alphanums,alphas,Literal,Group,Optional,ZeroOrMore,OneOrMore,Forward,dblQuotedString,ParseException,nums,QuotedString
import sys
class MEASUREParser:
    def __init__(self):

        ## Grammar definition
        # literals
        self.var_list = dict()
        period = Literal(".")

        variable = Word(alphas, alphanums + "."+ "_")
        number = Word(nums+".")
        integer = Word(nums)
        float = Combine(integer + "." + integer)
        ipAddress = Combine(Word(nums) + ('.' + Word(nums))*3)
        quote = (Literal("\"").suppress()|Literal("'").suppress())
        string = quote + Regex(r'(?:[^"\n\r\\]|(?:"")|(?:\\x[0-9a-fA-F]+)|(?:\\.))*') + quote

        # special characters
        oparen = Literal("(").suppress()
        eparen = Literal(")").suppress()
        semicolon = Literal(";").suppress()
        comma = Literal(",").suppress()
        obrace = Literal("{").suppress()
        ebrace = Literal("}").suppress()
        to = Literal("->")


        # section literals
        measurements = Literal("measurements").suppress()
        zoneTok = Literal("zones").suppress()
        actionTok = Literal("actions").suppress()

        # arithmetic literals
        eq = Literal("=")
        geq = Literal(">=")
        leq = Literal("<=")
        gt = Literal(">")
        lt = Literal("<")
        minus = Literal("-")
        plus = Literal("+")
        _and = (Literal("&&")|Literal("and"))
        _or = (Literal("||")|Literal("or"))
        _not = (Literal("!")|Literal("not"))

        # Productions for measurement definitions
#        paramExpr = Group(Optional(((variable)("pname") + eq.suppress() + (number|variable|dblQuotedString)("pval")) + ZeroOrMore(comma + (number|variable|dblQuotedString)("p"))))

        namedParam = Group((variable)("pname") + eq.suppress() + (ipAddress("pipaddr")|float("pfloat")|integer("pint")|variable("pvar")) + Optional(comma))("param")
        paramExpr =  Group(ZeroOrMore(namedParam))("params")
        functionExpr = Group(variable("fname") + oparen + paramExpr + eparen )("function")


        measurementExpr = Group(variable("mvar") + eq.suppress() + (functionExpr) + semicolon)("measure")
        measurementList = OneOrMore(measurementExpr)
        measure = Group(measurements + obrace + measurementList + ebrace)("measurements")



        # Productions for zone definitions
        arithParamExpr = Group(Optional((number|variable|string)("param") + ZeroOrMore(comma + (number|variable|string)("param"))))

        arithNamedParam = Group((variable)("pname") + eq.suppress() +
                              (ipAddress("pipaddr")|float("pfloat")|integer("pint")|variable("pvar")|dblQuotedString("pstr"))
                              + Optional(comma))("param")
        arithParamExpr =  Group(ZeroOrMore(arithNamedParam))("params")

        arithFuncExpr = Group(variable("fname") + oparen + arithParamExpr("params") + eparen)("function")
        arithTok = (arithFuncExpr|number("num")|variable("var"))
        opExpr = (eq|geq|leq|gt|lt|minus|plus|_and|_or)
        arithExpr = Forward()
        arithExpr << Group(oparen + Group((arithTok|arithExpr))("l") + opExpr("op") + Group((arithTok|arithExpr))("r") + eparen)("expression")

        zoneExpr = Group(variable("zname") + eq.suppress() + arithExpr + semicolon)("zone")
        zones = Group(zoneTok + obrace + OneOrMore(zoneExpr) + ebrace)("zones")

        # Productions for action definitions
        actNamedParam = Group((variable)("pname") + eq.suppress() +
                              (ipAddress("pipaddr")|float("pfloat")|integer("pint")|variable("pvar")|dblQuotedString("pstr"))
                              + Optional(comma))("param")
        actParamExpr =  Group(ZeroOrMore(actNamedParam))("params")

        actFunExpr = Group(variable("fname") + oparen + actParamExpr + eparen + semicolon)("function")

        state = variable("state")
        statetrans = Group(variable("from") + to.suppress() + variable("to"))("trans")
        fsm = (statetrans|state)

        action = Group(fsm + eq.suppress() + Group(OneOrMore(actFunExpr))("functions"))("action")
        actions = Group(actionTok + obrace + OneOrMore(action) + ebrace)("actions")

        self.MEASURE = measure + zones + actions

        self.actionFunctions = [
            {"fname":"Publish",
             "parameters": [
                 {"pname":"topic","type":"pstr"},
                 {"pname":"message","type":"pstr"},
             ]},
            {"fname":"Notify",
             "parameters": [
                 {"pname":"target","type":"pstr"},
                 {"pname":"message","type":"pstr"},
             ]}
        ]

        self.zoneFunctions = [
            {"fname":"AVG",
             "parameters": [
                 {"pname":"val","type":"pvar"},
                 {"pname":"max_age","type":"pstr"},
             ]}
        ]

        self.measureFunctions = [
            {"fname":"delay.twoway.icmp.us.mean",
             "parameters": [
                 {"pname":"source.ipv4","type":"pipaddr"},
                 {"pname":"destination.ipv4","type":"pipaddr"},
                 {"pname":"count","type":"pint"}
             ]},
            {"fname":"overload.risk.rx",
             "parameters": [
                 {"pname":"interface","type":"pvar"}
             ]}
        ]



        # convert to JSON
    def _functionToDict(self,function):
        f=dict()
        f['fname'] = function['fname']
        if 'params' not in function:
            return f
        params = function['params']
        f['params'] = list()
        for param in params:
            if all (k in param for k in ("pname","pvar")):
                m = dict(pname=param["pname"], pvar=param['pvar'].replace("\"",""))
                f['params'].append(m)
            elif all (k in param for k in ("pname","pint")):
                m = dict(pname=param["pname"], pint=int(param['pint'].replace("\"","")))
                f['params'].append(m)

            elif all (k in param for k in ("pname","pfloat")):
                m = dict(pname=param["pname"], pfloat=float(param['pfloat'].replace("\"","")))
                f['params'].append(m)

            elif all (k in param for k in ("pname","pipaddr")):
                m = dict(pname=param["pname"], pipaddr=param['pipaddr'].replace("\"",""))
                f['params'].append(m)
            elif all (k in param for k in ("pname","pstr")):
                m = dict(pname=param["pname"], pstr=param['pstr'].replace("\"",""))
                f['params'].append(m)
            else:
                print("Unknown field in param")
                sys.exit(1)
        return f


    def _actionsToDict(self,parseres):
        actions = list()
        for action in parseres['actions']:
    #        print(action.asXML())
            act = dict()
            if "state" in action:
                act['state'] = {"in":action['state']}
            elif "trans" in action:
                act['state'] = {"from":action['trans']['from'], "to":action['trans']['to']}
            else:
                print("missing state or trans in action")
                sys.exit(1)

            funclist = list()
            for function in action['functions']:
                fnc = self._functionToDict(function)
                funclist.append(fnc)
            act['functions'] = funclist
            actions.append(act)

        return actions


    def _parseExpression(self,expression):
        exp = dict()
        if "expression" in expression:
            return self._parseExpression(expression['expression'])
        elif all (k in expression for k in ("l","r","op")):

            exp['l'] = self._parseExpression(expression['l'])
            exp['op'] = expression['op']
            exp['r'] = self._parseExpression(expression['r'])
        elif "function" in expression:
            return {"function":self._functionToDict(expression['function'])}
        elif "num" in expression:
            return {"pval":float(expression['num'])}
        else:
            print("Unknown element in expression: ", expression.asXML())
            sys.exit(1)
        return exp

    def _zonesToDict(self,parseres):
        zones = list()

        for zone in parseres['zones']:
            z = dict()
            z[zone['zname']] = self._parseExpression(zone['expression'])
            zones.append(z)
        return zones

    def _measurementToDict(self,parseres):
        measurements = list()
        for measure in parseres['measurements']:
            if all (k in measure for k in ("mvar","mname")):
                m = dict(mvar=measure["mvar"], mname=measure['mname'].replace("\"",""))
                measurements.append(m)

            if all (k in measure for k in ("mvar","function")):
                measurements.append(dict(mvar=measure["mvar"], function=self._functionToDict(measure['function'])))
        return measurements


    def parse(self,source):
        try:
            malTokens = self.MEASURE.parseString(source)
            return malTokens
        except ParseException as e:
            raise e

    def parseToXML(self,source):
        try:
            res = self.MEASURE.parseString(source)
            return res.asXML()
        except ParseException as e:
            raise e

    def parseToDict(self,source):
        try:
            res = self.MEASURE.parseString(source)
            mpy = dict()
            mpy['measurements'] = self._measurementToDict(res)
            mpy['actions'] = self._actionsToDict(res)
            mpy['zones'] = self._zonesToDict(res)
            return mpy
        except ParseException as e:
            raise e

    def parseToJSON(self,source):
        import json
        try:
            res = self.MEASURE.parseString(source)
            mpy = dict()
            mpy['measurements'] = self._measurementToDict(res)
            mpy['actions'] = self._actionsToDict(res)
            mpy['zones'] = self._zonesToDict(res)
            return json.dumps({"MEASURE":mpy})
        except ParseException as e:
            raise e

    def parseToYAML(self,source):
        import yaml
        try:
            res = self.MEASURE.parseString(source)
            mpy = dict()
            mpy['measurements'] = self._measurementToDict(res)
            mpy['actions'] = self._actionsToDict(res)
            mpy['zones'] = self._zonesToDict(res)
            return yaml.dump({"MEASURE":mpy})
        except ParseException as e:
            raise e



def find_tool(metric):
    import json,pprint
    with open("repository.json") as json_file:
        json_data = json.load(json_file)
        pprint.pprint(json_data)

    for tool in json_data['tools']:
        for v in json_data['tools'][tool]['results']:
            if v == metric:
                return tool
    return False


def main():
    mString = "measurements { \n" \
              "  m1 = delay.twoway.icmp.us.mean(source.ipv4 = 1.2.3.4, destination.ipv4 = 4.3.2.1, count = 100, freq = 0.4); \n" \
              "  m2 = overload.risk.rx(interface = eth0);\n" \
              "}\n"
    zString =  "zones { \n" \
               " z1 = ((AVG(val = m1, max_age = \"1 minute\") + 10.0) < 10);\n" \
               " z2 = (AVG(val = m2, max_age = \"5 minute\") < 0.05);\n" \
               " z3 = (AVG(val = m1, max_age = \"5 minute\") > 10.0);\n" \
               "}\n"

    aString = "actions { \n" \
              " z1 = Notify(target = \"controller\", message = \"we are in z1\"); Publish(topic = \"alarms\", message = \"warning\");\n" \
              " z2 = Notify(target = \"controller\", message = \"we are in z2\");\n" \
              " z3 = Notify(target = \"controller\", message = \"we are in z3\");\n" \
              " z1->z3 = Notify(target = \"controller\", message = \"we are in z3\");\n" \
              "}\n"

    MALTestString = mString + zString + aString

    print("Input MEASURE string: \n",MALTestString)


    mparse = MEASUREParser()

    try:
        print("##############################")
        print("Parsing to PyParsing ParseResults")
        print("##############################")
        res = mparse.parse(MALTestString)
        print(res)
    except ParseException as e:
        print("Parse error: ",e)
        print(e.markInputline())
        sys.exit(1)

    mvarlist = list()
    for measure in res['measurements']:
        if measure['mvar'] not in mvarlist:
            mvarlist.append(measure['mvar'])
        else:
            sys.exit(1)

    try:
        print("##############################")
        print("Parsing to Python Dictionaries")
        print("##############################")
        res = mparse.parseToDict(MALTestString)
    except ParseException as e:
        print("Parse error: ",e)
        print(e.markInputline())
        sys.exit(1)

    import pprint
    pprint.pprint(res)

    try:
        print("##############################")
        print("Parsing to XML")
        print("##############################")
        res = mparse.parseToXML(MALTestString)
        print(res)
    except ParseException as e:
        print("Parse error: ",e)
        print(e.markInputline())
        sys.exit(1)

    try:
        print("##############################")
        print("Parsing to JSON")
        print("##############################")

        res = mparse.parseToJSON(MALTestString)
        print(res)
    except ParseException as e:
        print("Parse error: ",e)
        print(e.markInputline())
        sys.exit(1)


    try:
        print("##############################")
        print("Parsing to YAML")
        print("##############################")
        res = mparse.parseToYAML(MALTestString)
        print(res)
    except ParseException as e:
        print("Parse error: ",e)
        print(e.markInputline())
        sys.exit(1)


if __name__ == '__main__':
    main()



