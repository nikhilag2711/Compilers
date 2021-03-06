from collections import OrderedDict
from TypeTable import TypeTable
import json
import copy

# Structure of each entry of the symbol table --
# line: contains the line number where variable was declared
# check: For usual variables, the value for this will be 'VAR', for functions it will be 'FUNC',
#        for structs, it will be "STRUCT" and for unions, it will be "UNION"
#         Yet to decide regarding structs, enums and unions
# type: if check == 'VAR' -> this field contains the data type of the variable
#       if check == 'FUNC' -> this field contains the return type of the function
# params: if check == 'VAR' -> this field is not available or contains none
#         if check == 'FUNC' -> this field points to a dict where key is parameter names and the
#                               corresponding value is the type of the parameter
# value: stores the value of the of the entry (valid only if check == 'VAR')
# Any other temporary attribute can be stored with temp_<attr_name> just to denote that it is
# temporary 
#       

class SymbolTable() :
    def __init__(self):
        self.Table = []
        self.TopScope = OrderedDict()
        self.TT = TypeTable()
        self.error = False
        self.offset = 0
        self.offsetList = []
        self.flag = 0 # 1 means adding struct name, 0 means going inside symbol table,2 means adding var inside struct
        
    
    def InsertSymbol(self, iden, line_num, type_name=None):
        
        if self.flag == 0:
            found, entry = self.FindSymbolInCurrentScope(iden)
            if not found:
                found = self.FindSymbolInTable(iden,1)
                if found:
                    print("\33[33mPlease Note:\033[0m", iden, "on line", line_num, "is already declared at line", found[1]["line"])
                self.TopScope[iden] = OrderedDict()
                self.TopScope[iden]['line'] = line_num
            else:
                print("\033[91mError:\033[0m Redeclaration of existing variable", iden,". Prior declaration is at line", found["line"])
                self.error = True
        elif self.flag == 1:
            self.TT.InsertSymbol(iden,type_name, line_num, 1)
            self.error = self.error or self.TT.error
        else: # flag 2
            self.TT.InsertSymbol(iden,None, line_num, 2)
            self.error = self.error or self.TT.error

    def FindSymbolInTable(self, iden, path):
        Level_int = 1

        if path == 1:
            for Tree in reversed(self.Table):
                if Tree is not None and Tree.__contains__(iden):
                    return abs(Level_int-len(self.Table)), Tree.get(iden)
                Level_int += 1

        elif path == 2:
            for Tree in reversed(self.Table):
                if Tree is not None and Tree.__contains__(iden):
                    return Tree.get(iden), Tree[iden]

        if path == 2:
            return False, []
        elif path == 1:
            return False

    def FindSymbolInCurrentScope(self, iden):
        found = self.TopScope.get(iden, False)
        if found:
            return found, self.TopScope[iden]
        else:
            return found, []

    def PushScope(self, TAC):

        self.offsetList.append(self.offset)

        #new work
        esp_ptr = -20
        for item in self.TopScope.keys():
            if item!= '#scope' and item!='#StructOrUnion' and item!='#scopeNum' and 'temp' in self.TopScope[item].keys() and self.TopScope[item]['temp'][0]=='-':
                esp_ptr = min(esp_ptr, int(self.TopScope[item]['temp'].split('(')[0])) 
        self.lastScopeTemp = esp_ptr
        ####

        if len(self.Table) == 0:
            self.Table.append(self.TopScope)
            TopScopeName = list(self.TopScope.items())[-1][0]
            if TopScopeName != '#StructOrUnion':
                self.TopScope = list(self.TopScope.items())[-1][1]
                if '#scope' not in self.TopScope:
                    self.TopScope['#scope'] = []
                parScopeList = self.TopScope['#scope']
                parScopeList.append(OrderedDict())
                self.TopScope = parScopeList[-1]
        else:
            
            if '#scope' not in self.TopScope:
                self.TopScope['#scope'] = []
            
            parScopeList = self.TopScope['#scope']
            self.Table.append(self.TopScope)
            parScopeList.append(OrderedDict())
            self.TopScope = parScopeList[-1]
        
        self.TT.PushScope()
        ###
        TAC.scope_counter += 1
        TAC.scope_list[TAC.scope_counter] = []
        self.TopScope['#scopeNum'] = TAC.scope_counter
        TAC.scope_list[self.TopScope['#scopeNum']].append(TAC.nextstat)
        TAC.emit('PushScope','','','')
        ###
        self.error = self.error or self.TT.error
        return

    def StoreResults(self, TAC):
        self.error = self.error or self.TT.error
        self.TopScope['#StructOrUnion'] = dict(self.TT.TopScope)
        self.PushScope(TAC)
        TAC.final_code.pop()
        return

    def PopScope(self, TAC, flag = None):
        # new work
        # print(json.dumps(self.TopScope,indent=2))
        esp_ptr = self.lastScopeTemp
        if self.TopScope:
            for item in self.TopScope.keys():
                if item!= '#scope' and item!='#StructOrUnion' and item!='#scopeNum' and 'temp' in self.TopScope[item].keys() and self.TopScope[item]['temp'][0]=='-':
                    esp_ptr = min(esp_ptr, int(self.TopScope[item]['temp'].split('(')[0]))
        ## patching lines for current scope
            for lines in TAC.scope_list[self.TopScope['#scopeNum']]:
                TAC.final_code[lines] = ['UNARY&', '%esp', f'{esp_ptr}(%ebp)', '']

        ## adding dummy line for previous scope
            if len(self.Table)>1 and flag is None:
                prev_scope_num = self.Table[-1]['#scopeNum']
                TAC.scope_list[prev_scope_num].append(TAC.nextstat)
                TAC.emit('PushScope','','','')
            # elif len(self.Table)==1:
            #     print(json.dumps(self.Table,indent=2))
        ##
        self.TopScope['#StructOrUnion'] = dict(self.TT.TopScope)
        self.TT.PopScope()
        self.error = self.error or self.TT.error
        TScope = self.TopScope
        self.offset = self.offsetList[-1]
        self.offsetList.pop()

        if len(self.Table) > 0:
            self.TopScope = self.Table.pop()
        else:
            self.TopScope = None
        return TScope

    def DelStructOrUnion(self, tmp):
        list_copy = []
        for item in tmp["#scope"]:
            item.pop('#StructOrUnion', None)
            if "#scope" in item:
                self.DelStructOrUnion(item)
            if not item:
                continue
            list_copy.append(item)
        if len(list_copy) == 0:
            tmp.pop('#scope', None)
        else:
            tmp['#scope'] = list_copy

    def PrintTable(self):
        # print(json.dumps(self.Table[0], indent=2))

        print("Global Symbol Table : ")
        for key, value in self.Table[0].items():
            if key != "#StructOrUnion" and key!= '#scopeNum':
                print(key)
                for key2, value2 in value.items():
                    if key2 != "#scope":
                        print(f'"{key2}" : {value2}')
                print("\n")
            # else:
            #     print(key, value)

        for key, value in self.Table[0].items():
            if key !='#scopeNum':
                if "#scope" in value:
                    tmp = copy.deepcopy(value["#scope"][0])
                    del tmp['#StructOrUnion']
                    if "#scope" in tmp:
                        self.DelStructOrUnion(tmp)
    
                    if len(tmp) > 0:
                        print(f'Local Symbol Table for "{key}":')
                        print(json.dumps(tmp, indent=2))
                        print("\n")
            else:
                print(key, value)

    def ModifySymbol(self, iden, field, val, statement_line=None):
        if self.flag == 0:
            found, entry = self.FindSymbolInCurrentScope(iden)
            if found:
                self.TopScope[iden][field] = val
                if field == "sizeAllocInBytes":
                    if len(self.Table) > 0:
                        self.TopScope[iden]["offset"] = self.offset
                        # val = (val + 3) // 4
                        # val = val * 4
                        self.offset += val
                elif field == "vars":
                    if len(self.Table) > 0:
                        curOffset = 0
                        for var in self.TopScope[iden][field]:
                            self.TopScope[iden][field][var]["offset"] = curOffset
                            curOffset += self.TopScope[iden][field][var]["sizeAllocInBytes"]
                return True

            else:
                found, entry = self.FindSymbolInTable(iden,2)
                if found:
                    found[field] = val
                    if field == "sizeAllocInBytes":
                        if len(self.Table) > 0:
                            self.TopScope[iden]["offset"] = self.offset
                            # val = (val + 3) // 4
                            # val = val * 4          
                            self.offset += val
                    elif field == "vars":
                        if len(self.Table) > 0:
                            curOffset = 0
                            for var in self.TopScope[iden][field]:
                                self.TopScope[iden][field][var]["offset"] = curOffset
                                curOffset += self.TopScope[iden][field][var]["sizeAllocInBytes"]
                    return True
                else:
                    if statement_line:
                        print(f'Tried to modify the {field} of the undeclared symbol {iden} on line {statement_line}')
                    else:
                        print(f'Tried to modify the {field} of the undeclared symbol {iden}')
                    self.error = True
                    return False
        elif self.flag == 1:
            self.TT.ModifySymbol(iden, field, val, statement_line, 1)
            self.error = self.error or self.TT.error
        else: # flag = 2
            self.TT.ModifySymbol(iden, field, val, statement_line, 2)
            self.error = self.error or self.TT.error
        
    def ReturnSymTabEntry(self, iden, statement_line=None):
        found, entry = self.FindSymbolInCurrentScope(iden)
        if found:
            return found, entry
        else:
            found, entry = self.FindSymbolInTable(iden, 2)
            if found:
                return found, entry
            else:
                print(f'\033[91mError:\033[0m The variable {iden} on line {statement_line} is not declared.')
                self.error = True
                return None,None
        
    def isGlobal(self, iden =None):
        if len(self.Table) == 0:
            return True
        else:
            return False
