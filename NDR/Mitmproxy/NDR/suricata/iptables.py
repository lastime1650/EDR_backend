import subprocess


def clean_iptables():
    
    chains = [
        ["iptables", "-L", "INPUT"],
        ["iptables", "-L", "OUTPUT"],
        ["iptables", "-L", "FORWARD"],
        ["iptables", "-L", "PREROUTING" , "-t", "nat"],
        ["iptables", "-L", "POSTROUTING" , "-t", "nat"],
    ]
    
    for chain in chains:
        
        chain_name = chain[2]
        
        R = subprocess.run(
            chain, 
            text=True, capture_output=True, check=True
            )
        
        T = R.stdout.splitlines()
        
        if len(T) < 3:
            continue
        T = T[2:]
        
        rules = []
        
        for infos in T:
            #print(infos)
            
            rule:list[str] = []
            
            #print(bytes(infos.encode()))
            
            tmp_str =""
            index = False
            current_32 = False
            for byte_letter in bytes(infos.encode()):
                if byte_letter != 32:
                    tmp_str += str(chr(byte_letter))
                else:
                    if len(tmp_str)>0:
                        rule.append(
                            tmp_str
                        )
                        tmp_str = ""
            if len(rule) != 0:
                rule.append( tmp_str )
                tmp_str= ""
        
            rules.append(
                rule
            )
        
        remove_count = 0
        for i, rule in enumerate(rules):
            
            i += 1
            
            if len(rule) == 0:
                continue
            target_name = rule[0]
            if "DOCKER" in target_name or "MASQUERADE" in target_name:
                continue
            
            # 삭제
            remove_rule_id = i - remove_count
            
            r1 = ["iptables", "-D", chain_name, str(remove_rule_id)]
            if chain_name == "PREROUTING" or chain_name == "POSTROUTING":
                r1 += ["-t", "nat"]
            
            subprocess.run(
                r1, 
                capture_output=True,
                text=True,
                check=True
            )
            
            remove_count += 1
            
        
        print(T)
    

#
#
class IptablesRule():
    def __init__(self):
        self.commandline = []
        
    def Print(self):
        print(self.commandline)

    def Clean_Rule_Commandline(self):
        self.commandline = []
    
    def Add_source_ip(self, ip:str):
        self.commandline += ["-s", ip]
    
    def Add_destination_ip(self, ip:str):
        self.commandline += ["-d", ip]
    
    def Add_source_port(self, protocol:str,port:int):
        self.commandline += ["-p", protocol, "--sport", str(port)]
    
    def Add_destination_port(self, protocol:str, port:int):
        self.commandline += ["-p", protocol, "--dport", str(port)]
        
    def Add_ACCEPT(self):
        self.commandline += ["-j", "ACCEPT"]
    def Add_DROP(self):
        self.commandline += ["-j", "DROP"]
        
    def Add_source_interface(self, interface_name:str):
        self.commandline += ["-i", interface_name]
        
    def Add_destination_interface(self, interface_name:str):
        self.commandline += ["-o", interface_name]
        
    ######
    def init__Add_Rule_INPUT( self):
        chain_name = "INPUT"
        self.commandline = ["iptables", "-I", chain_name] 
        
    def init__Add_Rule_OUTPUT( self):
        chain_name = "OUTPUT"
        self.commandline = ["iptables", "-I", chain_name]
        
    def init__Add_Rule_FORWARD( self):
        chain_name = "FORWARD"
        self.commandline = ["iptables", "-I", chain_name]
        
        
        
    def init__Add_Rule_PREROUTING( self):
        chain_name = "PREROUTING"
        self.commandline = ["iptables", "-t", "nat", "-I", chain_name] 
        
    def init__Add_Rule_POSTROUTING( self, ):
        chain_name = "POSTROUTING"
        self.commandline = ["iptables", "-t", "nat", "-I", chain_name] 


    def Run_Rule(self):
        return subprocess.run(
                self.commandline, 
                capture_output=True,
                text=True,
                check=True
            ).stdout

        
clean_iptables()