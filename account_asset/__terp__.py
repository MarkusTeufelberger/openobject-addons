# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Asset management",
    "version" : "1.1",
    "depends" : ["account", "account_simulation"],
    "author" : "Tiny, Grzegorz Grzelak (Cirrus.pl)",
    "description": """Financial and accounting asset management.
    Allows to define
    * Asset category. 
    * Assets.
    * Asset usage period and method.
    * Asset method types
    * Default accounts for methods and categories
    * Depreciation methods:
        - Straight-Line
        - Declining-Balance
        - Sum of Year Digits
        - Units of Production - this method can be used for individual depreciation schedule.
        - Progressive
    * Method Parameters:
	- Starting period
	- Number of depreciation intervals
	- Number of intervals per year
	- Progressive factor for Declining-Balance method
	- Salvage Value
	- Life Quantity for Unit of Production method
    * Functionality:
	- Defining the asset in invoice when purchasing
	- Adjusting the asset value in purchasing Refund
	- Periodical units of production entering
	- Periodical asset calculation
	- Sale invoice stops the depreciation and make final postings
    * Wizards:
	- Initial Values for continuing depreciation of previous system
	- Revaluation
	- Abandonment
	- Method parameters changing
	- Suppressing and Resuming depreciation
	- Localisation changing

This module is based on original Tiny module account_asset version 1.0 of the same name "Financial and accounting asset management".

Purpose of the module is to aid fixed assets management and integrate this management into the accounting system.

Terms used in the module:
- Asset - product or set of products which exist in company and are used internally for longer time and must be taken into asset register.
- Asset Category - Term for grouping assets into hierarchical structure.
- Asset Method - Calculation rules of depreciation. Asset can have few methods. For each asset element or for each kind of depreciation (cost and tax).
- Method Type - Used for differentiation of method types and for default settings. 
- Method Defaults - Settings assigned to method types (and categories) simplifying creation of asset settings.

Usage of the module:
====================
Introduction settings:
1. Creating Asset categories (optional)
2. Creating Method Types (optional)
3. Setting Method Defaults (optional)

Usual activities:
4. Creating Asset
5. Purchasing Asset
6. Calculating Asset depreciation

Rare activities:
7. Acquiring asset 
8. Sale of asset
9. Revaluation of asset
10. Asset abandonment
11. Suppressing and resuming the depreciation
12. Changing a localisation

============================
1. Create Asset categories in menu "Financial Management - Configuration - Assets - Asset Categories". Categories can be hierarchical. Read farther how hierarchy works for Method Defaults and for Periodical Calculation. You can check hierarchy of categories in menu "Financial Management - Configuration - Assets - Category Structure"

2. Create Method types in menu "Financial Management - Configuration - Assets - Asset Method Types". You should create method type for every kind of depreciation. Fe. you use fast depreciation for computer equipment and slow depreciation for buildings. You can also create different types for cost depreciation and for tax depreciation (if you use tax depreciation).

3. Create Method Defaults in menu "Financial Management - Configuration - Assets - Asset Method Defaults". You can create default settings for method type only or for pairs of method type and asset category. It is suggested to accounting manager to design asset categories hierarchy and assign defaults to categories and method types before system start. If it will be well designed accountants will have simplified and more error-proof job later on. All accounts, calculation methods and other parameters will be entered automatically during asset creation. Note that as Categories are hierarchical the defaults will work also hierarchical for all children categories. It means that if there are no defaults for certain pair of Method Type and Category system look for pairs of Method Type and parent Category. It looks for such pair till root of Category.

4. Create asset in menu "Financial Management - Configuration - Assets - Assets" or in "Financial Management - Assets - Assets". In Asset form you should enter the name of asset, asset code (abbreviation or numerical symbol which can be set in Sequence settings). Then you select Asset category. It is optional step but it would be used to enter method defaults. 

Then you go to methods creation. Asset can have many methods. They can be used when asset is the set of several elements. Fe. Computer set consisting PC, Screen and printer. When they have the same depreciation rule they can be in one method (invoice lines assigned to the same method). If they have different depreciation rules they have to be in different methods. 

As a first step in creation of method select Method Type. After Method Type selection many fields can be filled automatically. First system creates the method Name from Method Type Code, Asset name and Asset Code. It would simplify Method selection in invoice line. Then system fills other fields according to method defaults. There are accounts, calculation methods and other values. You can change Method name and other default settings before asset saving but when you select Method type again (even to the same type) these fields will be reverted back to defaults.

5. As buying is the most common way to possess the asset you usually have to assign the created asset method to supplier invoice line. So when you create the draft supplier invoice you have to open the invoice line and select the created asset method. Note that after asset method selection the invoice line account would be changed to Asset Account which was set in Asset method. Then when you create the invoice the asset state changes to Normal and Asset method state changes to Open and method is ready for depreciation.

When asset purchase is subject of refund and asset should change the value according to that you should assign Refund line to asset method as you did during Purchasing. Method value will be reflected to the refund value. 

6. To make asset calculation choose "Financial Management - Periodical Processing - Assets Calculation - Compute Assets". You have to select period of calculation and date of postings. Selected period is also used as posting period so Date must be in Period. Then you can select Asset Category and Method Type which you would like to compute. Remember that Categories are hierarchical and work for all children. 

7. When you possesed the asset different way than purchasing (by own production or investment) or you wish to continue depreciation started in other system you can use wizard Initial Values. If you continue depreciation you can enter Base Value as starting Total and Expense Value as depreciations already made. You can also Enter Base Value only as Residual left from previous depreciation (don't enter Expense Value in such case). For continuing depreciation you have to enter Residual Intervals. Intervals already calculated can be noted in Notes for history entry.

You can use this wizard also to make starting account move if asset was produced by you or is a result of investment recorded previously in other accounts. 

8. When asset is to be sold you can assign appropriate method to the Customer invoice line. System will make needed postings and stop the asset method.

9. If you wish to revalue the method you can use Revalue Method button. Select parameters for postings and for asset history.

10. If you wish to abandon the asset you can use Abandon Method button. Parameters in wizard are described in labels.

11. You can wish suppress or resume the depreciation. You can use Suppress and Resume buttons for that. If method has state different than "Open" it is not calculated.

12. Some local rules require to trace the asset localisation. You can use for that button "Change Localisation" on asset tab "Other Information". Wizard will change localisation text and make proper entry in asset history.

Remarks:
- All wizard actions are traced in Asset history. You can use Asset history as Asset register.
- If you make mistake in depreciations or in wizard actions you can delete created accounting moves usual way in Financial menu. They are in draft state after creation so can be deleted. You can recreate depreciation moves in Compute Asset wizard. Deleting the moves created by wizards doesn't delete asset history entries.
- You can also manually create account moves for special actions not covered by this module functionality. When creating such move you should assign asset method to move lines. You can use this possibility to add tax depreciation. Create special method type for tax. Then create tax method for asset and create manually account move with account move lines assigned to method with proper accounts.
- If you are not satisfied with calculation methods functionality or you wish to have individual depreciation schedule for method you can adopt Unit of Production calculation method for that. Enter 100 in Life Quantity and then you can use percentage values in method usage.
    """,
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/Accounting",
    "init_xml" : [
    ],
    "demo_xml" : [
    ],
    "update_xml" : [
        "security/ir.model.access.csv",
        "account_asset_wizard.xml",
        "account_asset_view.xml",
        "account_asset_invoice_view.xml"
    ],
#   "translations" : {
#       "fr": "i18n/french_fr.csv"
#   },
    "active": False,
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

