""""
#########################################################################################

   Author:         Petr Nemec
   Description:    This script reads policy-statements configuration from two routers
                   and identifies differences

   Date:           2017-03-03

#########################################################################################
"""

from pprint import pprint
from deepdiff import DeepDiff
import yaml
import getpass
from ncclient import manager
from ncclient.xml_ import *
import re
from bs4 import BeautifulSoup as Soup


def printline():
    """
    :param:         no params
    :return:        it prints simple line
    """
    print "----------------------------------------------------------"

def printstars():
    """
    :param:         no params
    :return:        it prints star line
    """
    print "\n***********************************************************"

def printhash():
    """
    :param:         no params
    :return:        it prints hash line
    """
    print "###########################################################"

def printeqsigns():
    """
    :param:         no params
    :return:        it prints equal sign line
    """
    print "==========================================================="

def samepolicy(first_str,second_str):
    """
    :param:         Policy names
    :return:        True or False - if policy counterpart is found
    """
    regex_p = re.compile(r"-PRIMARY", re.IGNORECASE)
    regex_s = re.compile(r"-SECONDARY", re.IGNORECASE)

    if first_str == second_str:
        return True
    # Check if policy name contains string "Primary" /ignore case sensitive characters
    elif re.search(regex_p, first_str, flags=0):
        if re.sub(regex_p,'', first_str) == re.sub(regex_s,'', second_str):
            return True
    # Check if policy name contains string "Secondary" /ignore case sensitive characters
    elif re.search(regex_s, first_str, flags=0):
        if re.sub(regex_s,'', first_str) == re.sub(regex_p,'', second_str):
            return True
    # Check if one policy contains "Secondary" and the other one has no adjective (Prim or Sec)
    elif re.search(regex_s, first_str, flags=0):
        if re.sub(regex_s,'', first_str) == second_str:
            return True
    # Check if one policy contains "Primary" and the other one has no adjective (Prim or Sec)
    elif re.search(regex_p, first_str, flags=0):
        if re.sub(regex_p,'', first_str) == first_str:
            return True
    else:
        return False

def metrictodict(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & metrics
                    Note metric is read from both sections "FROM" & "THEN"
    """
    metric_dic = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text
        for metric in term.findChildren('metric'):
            metric = metric.find('metric')
            if metric:
                metric_dic[termname] = metric.text
    return metric_dic

def metricvaluecheck(med_dic_a, med_dic_b, router_a, router_b):
    """
    :param:         Dictionary of terms & metrics and strings referring to router names
    :return:        Prints incorrect MED values
    """
    if not (all(int(value) == 100 for value in med_dic_a.values()) \
                    or all(int(value) == 150 for value in med_dic_a.values())):
        print "Metric values are inconsistent across all terms, MED complementary pair 150-100"
        for term in med_dic_a:
            print "%s, %s : MED %s" % (router_a, term, med_dic_a[term])

    if not (all(int(value) == 100 for value in med_dic_b.values()) \
                    or all(int(value) == 150 for value in med_dic_b.values())):
        print "Metric values are inconsistent across all terms, MED complementary pair 150-100"
        for term in med_dic_b:
            print "%s, %s : MED %s" % (router_b, term, med_dic_b[term])

    for term in med_dic_a:
        if term in med_dic_b:
            if med_dic_a[term] == med_dic_b[term]:
                print "%s: MED is same on both routers %s" % (term, med_dic_a[term])



def lpreftodict(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & local-preference
                    Note metric is read from both sections "FROM" & "THEN"
    """
    lpref_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text
        for lpref in term.findChildren('local-preference'):
            lpref = lpref.find('local-preference')
            if lpref:
                lpref_dict[termname] = lpref.text
    return lpref_dict

def lpvaluecheck(lp_dic_a, lp_dic_b, router_a, router_b):
    """
    :param:         Dictionary of terms & Local-preferences and strings referring to router names
    :return:        Prints incorrect MED values
    """
    if not (all(int(value) == 90 for value in lp_dic_a.values()) \
                    or all(int(value) == 150 for value in lp_dic_a.values())):
        print "Local-preference values are inconsistent across all terms, MED complementary pair 150-90"
        for term in lp_dic_a:
            print "%s, %s : LP %s" % (router_a, term, lp_dic_a[term])

    if not (all(int(value) == 90 for value in lp_dic_b.values()) \
                    or all(int(value) == 150 for value in lp_dic_b.values())):
        print "Local-preference values are inconsistent across all terms, MED complementary pair 150-90"
        for term in lp_dic_b:
            print "%s, %s : LP %s" % (router_b, term, lp_dic_b[term])

    for term in lp_dic_a:
        if term in lp_dic_b:
            if lp_dic_a[term] == lp_dic_b[term]:
                print "%s: Local-preference is same on both routers %s" % (term, lp_dic_a[term])


def protocoltodict(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & protocols
                    Note metric is read from both sections "FROM" & "THEN"
    """
    prot_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text
        protocol = term.findAll('protocol')
        prot_list = []
        if protocol:
            for i in range(len(protocol)):
                prot_list.append(protocol[i].text)
            prot_dict[termname] = prot_list
    return prot_dict

def from_commtodict(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & communities
                    Note metric is read only from the sections "FROM"
    """
    comm_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text

        for fr in term.findAll('from'):
            community = fr.findAll('community')
            comm_list = []
            if community:
                for i in range(len(community)):
                    comm_list.append(community[i].text)
                comm_dict[termname] = comm_list
    return comm_dict

def then_commtodict(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & communities
                    Note metric is read only from the sections "THEN"
    """
    comm_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text

        for th in term.findAll('then'):
            community = th.findAll('community-name')
            comm_list = []
            if community:
                for i in range(len(community)):
                    comm_list.append(community[i].text)
                comm_dict[termname] = comm_list
    return comm_dict

def routefiltodict(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & route-filters
                    Note metric is read from both sections "FROM" & "THEN"
    """
    routfil_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text
        rfilt = term.find_all('address')
        route_list = []
        for route in rfilt:
            if route:
                # combine prefix and exact, orlonger etc... into a list
                route_list.append([route.text, route.findNextSibling()])
            routfil_dict[termname] = route_list
    return routfil_dict

def from_pltodict(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & prefix-lists
                    Note metric is read only from the sections "FROM"
    """
    pl_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text

        for fr in term.findAll('from'):
            prefix = fr.findChildren('prefix-list')
            pl_list = []
            if prefix:
                for i in range(len(prefix)):
                    tmp = str(prefix[i].text)
                    pl_list.append(remove_tag(tmp))
                pl_dict[termname] = pl_list
    return pl_dict

def remove_tag(my_str):
    """
    :param:         String
    :return:        it removes "\n" characters
    """
    regex = re.compile(r"-\\n", re.IGNORECASE)
    return re.sub(regex, '', my_str, flags=0)

def then_accept(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & actions accept
                    Note metric is read only from the sections "THEN"
    """
    accept_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text

        for th in term.findAll('then'):
            accept = th.find('accept')
            if accept:
                accept_dict[termname] = "accept"
    return accept_dict

def then_reject(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & actions reject
                    Note metric is read only from the sections "THEN"
    """
    reject_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text

        for th in term.findAll('then'):
            reject = th.find('reject')
            if reject:
                reject_dict[termname] = "reject"
    return reject_dict

def then_next(policy):
    """
    :param:         Policy as the instance of class 'bs4.BeautifulSoup'
    :return:        Dictionary of terms & actions next term
                    Note metric is read only from the sections "THEN"
    """
    next_dict = {}
    for term in policy.find_all('term'):
        termname = "term " + term.findChild('name').text

        for th in term.findAll('then'):
            nextterm = th.find('next')
            if nextterm:
                next_dict[termname] = "next"
    return next_dict

def compare(itemname, first_dic, second_dic, router_a, router_b):
    """
    :param:         Dictionaries, router names and info what values are compared
    :return:        The function prints out the differences found in keys and values
    """
    # Test if the dictionaries and the items are the same
    ddiff = (DeepDiff(second_dic, first_dic, ignore_order=True))
    if ddiff.get('dictionary_item_added'):
        print itemname + " misconfigured:"
        print "This statement is missing on router: %s" % router_b
        pprint(ddiff['dictionary_item_added'])
        printline()

    if ddiff.get('dictionary_item_removed'):
        print itemname + " misconfigured:"
        print "This statement is missing on router: %s" % router_a
        pprint(ddiff['dictionary_item_removed'])
        printline()

    if ddiff.get('iterable_item_added'):
        print itemname + " misconfigured:"
        print "This statement is missing on router: %s" % router_b
        pprint(ddiff['iterable_item_added'])
        printline()

    if ddiff.get('iterable_item_removed'):
        print itemname + " misconfigured:"
        print "This statement is missing on router: %s" % router_a
        pprint(ddiff['iterable_item_removed'])
        printline()

def compare_kyes_only(itemname, first_dic, second_dic, router_a, router_b):
    """
    :param:         Dictionaries, router names and info what values are compared
    :return:        The function prints out the differences found in keyz
    """
    # Test if the dictionaries and the items are the same
    ddiff = (DeepDiff(second_dic, first_dic, ignore_order=True))
    if ddiff.get('dictionary_item_added'):
        print itemname + " misconfigured:"
        print "This statement is missing on router: %s" % router_b
        pprint(ddiff['dictionary_item_added'])
        printline()

    if ddiff.get('dictionary_item_removed'):
        print itemname + " misconfigured:"
        print "This statement is missing on router: %s" % router_a
        pprint(ddiff['dictionary_item_removed'])
        printline()


def main():

    f = open('config/routers.yml')
    s = f.read()
    routers = yaml.load(s)
    f.close()

    pol_list = []
    rlist = []


    for router in routers:


        print "\nReady to get policies configured on the router " + routers[router]["name"]
        # Enter username or use default one defined in *.yang
        routers[router]["username"] = raw_input("Username[%s]: " % (routers[router]["username"])) or routers[router]["username"]
        routers[router]["password"] = getpass.getpass(prompt='Password: ', stream=None)


        # establish NETCONF session /w router or switch
        dev = manager.connect(host=routers[router]['ip'],
            port=22,
            username=routers[router]["username"],
            password=routers[router]["password"],
            timeout=10,
            device_params = {'name':'junos'},
            hostkey_verify=False)

        # retrieve full config
        # result_xml = router.get_configuration(format='xml')

        # Define a filter to narrow down the output retrieved from router
        config_filter = new_ele('configuration')
        system_ele = sub_ele(config_filter, 'policy-options')
        sub_ele(system_ele, 'policy-statement')

        # Retrieve only specific part of configuration defined by config_filter
        policycfg = dev.get_configuration(format='xml', filter=config_filter)

        dev.close_session()

        # Convert xml into the instacke of class bs4.BeautifulSoup
        dpolicysum = Soup(policycfg.tostring, 'xml')

        # Attach the dictionary it into a list
        pol_list.append(dpolicysum)

        # Attach router name into a list to distinguish "first" and "second"
        rlist.append(routers[router]["name"])


    # Split list into two dictionaries referring to each router
    first = pol_list[0]
    second = pol_list[1]


    for policy_a in first.find_all('policy-statement'):
        # Print policy name
        printeqsigns()
        print "Checking policy %s" % policy_a.find('name').text

        policy_b_exist = False
        # Search for appropriate policy on other router
        for policy_b in second.find_all('policy-statement'):

            # Accept -PRIMARY & -SECONDARY differences in names
            if samepolicy(policy_a.find('name').text, policy_b.find('name').text):
                policy_b_exist = True
                print "Policy pair found: %s %s" % (policy_a.find('name').text, policy_b.find('name').text)


                # Test MED if all are the same on one router (100 or 150)
                metricvaluecheck(metrictodict(policy_a), metrictodict(policy_b), rlist[0], rlist[1])


                compare_kyes_only("MED", protocoltodict(policy_a), protocoltodict(policy_b),
                        rlist[0], rlist[1])



                # Test LP if all are the same on one router (150 or 90)
                lpvaluecheck(lpreftodict(policy_a), lpreftodict(policy_b), rlist[0], rlist[1])

                compare_kyes_only("Local-preference", protocoltodict(policy_a), protocoltodict(policy_b),
                        rlist[0], rlist[1])



                # Test "from protocols"
                compare("Protocols", protocoltodict(policy_a), protocoltodict(policy_b),
                        rlist[0], rlist[1])


                # Test "from cummunity"
                compare("FROM community", from_commtodict(policy_a), from_commtodict(policy_b),
                        rlist[0], rlist[1])


                # Test "then cummunity"
                compare("THEN community", then_commtodict(policy_a), then_commtodict(policy_b),
                        rlist[0], rlist[1])


                # Test "from route-filter"
                compare("Route-filter", routefiltodict(policy_a), routefiltodict(policy_b),
                        rlist[0], rlist[1])


                # Test "from prefix-list"
                compare("Prefix-list-filter", from_pltodict(policy_a), from_pltodict(policy_b),
                        rlist[0], rlist[1])


                # Test "accept" action
                compare("Action accept", then_accept(policy_a), then_accept(policy_b),
                        rlist[0], rlist[1])


                # Test "reject" action
                compare("Action reject", then_reject(policy_a), then_reject(policy_b),
                        rlist[0], rlist[1])

                # Test "next term" action
                compare("Action next term", then_next(policy_a), then_next(policy_b),
                        rlist[0], rlist[1])



        if not policy_b_exist:
            print "No complementary policy found"



if __name__ == "__main__":
        main()
