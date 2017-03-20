


bs4
===
NetOps scripts utilising Beautiful Soup Python library as a tool to parse XML obtained from NETCONF messages.

There are a few Python scripts created by using ncclient and bs4 module which may help with checking the consistency of configuration applied on two MPLS-PE routers.

 
 **PolicyCheck**
 ----------
This script is intended to be used for comparing the policies on PE routers. In scenarios like that one shown in the picture where routes are advertised to MPLS domain from two PE routers both routers router_a and Router_b we could theoretical want one of those routers make acting as primary (forwarding data back and forth to MPLS) as shown in picture A and the other one as standby waiting for failover in case of primary router fails (shown in picture B).

Explicit policy definition may help routers to avoid using sub-optimal or asymmetric path when forwarding data among MPLS PE routers. 

![Router_a is primary](https://github.com/czpene1/bs4/blob/master/PolicyCheck/PE_traffic.png)

To achieve that we can configure so called VRF import/export polices under routing-instance statement to influence which path data will follow by modyfying BGP attributes such as local-preference, MED atc.

In fact there may be also policies configured to influence which routes from external BGP neighbors such as firewalls will be installed into routing table and which routes will be advertised to them. These are often also referred to as import/export policies applied to specific BGP neighbors.

A problem may arise when import & export policies are not consistent. Then some after failover some traffic may be blackholed due to incorrect or missing statements. 

Router-a & Router_b (VRF definition will be the same)

    admin@router-A> show configuration routing-instances VRF-A {
        instance-type vrf;
        vrf-import VRF-A-IMPORT;
        vrf-export VRF-A-EXPORT;
        protocols {
            bgp {
                group EXTERNAL {
                    neighbor 1.2.3.4 {
                        import VRF-A-FW-IN;
                        export VRF-A-FW-OUT;
                        peer-as 65123;
                    }
                }
            }
        }


Router-A (**primary router**) - MP-IBGP policies (MPLS)

    admin@router-A> show configuration policy-options
    
    policy-statement VRF-A-EXPORT {
        term 1 {
            then {
                local-preference 150;
                accept;
            }
        }
        term 2 {
            then reject;
        }
    }
    policy-statement VRF-A-IMPORT {
        term 1 {
            from community ABC-COMM;
            then accept;
        }
        term 2 {
            then reject;
        }
    }



Router-B (**secondary router**) - MP-IBGP policies (MPLS)

    admin@router-B> show configuration policy-options
    
    policy-statement VRF-A-EXPORT {
        term 1 {
            then {
                local-preference 90;
                accept;
            }
        }
        term 2 {
            then reject;
        }
    }
    policy-statement VRF-A-IMPORT {
        term 1 {
            from community ABC-COMM;
    	then accept;
    	
        }
        term 2 {
            then reject;
        }
    }

    
Router_a (**primary router**) - EBGP policy (FW)

      admin@router-A> show configuration policy-options
    
    policy-statement VRF-A-FW-IN {
        term 1 {
            from {
                protocol bgp;
                prefix-list TEST-PL;
            }
            then {
                local-preference 150;
                accept;
            }
        }
        term 2 {
            then reject;
        }
    }
    admin@router-A> show configuration policy-options
    
    policy-statement VRF-A-FW-OUT {
        term 1 {
            then {
                metric 100;
                accept;
            }
        }
        term 2 {
            then reject;
        }
    }
    
    
Router_b (**secondary router**) - EBGP policy (FW)


    admin@router-B> show configuration policy-options
    
    policy-statement VRF-A-FW-IN {
        term 1 {
            from {
                protocol bgp;
                prefix-list TEST-PL;
            }
            then {
                local-preference 90;
                accept;
            }
        }
        term 2 {
            then reject;
        }
    }
    
    
    admin@router-B> show configuration policy-options
    
    policy-statement VRF-A-FW-OUT {
        term 1 {
            then {
                metric 150;
                as-path-prepend "65001 65001 65001";
                accept;
            }
        }
        term 2 {
            then reject;
        }
    }

These basic constructs may be extended with prefix-lists, route-filters, protocols from which routes are redistributed etc.


----------
