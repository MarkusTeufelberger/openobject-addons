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
    "depends" : ["account"],
    "author" : "Tiny, Grzegorz Grzelak (Cirrus.pl)",
    "description": """Financial and accounting asset management.
    Allows to define
    * Assets.
    * Asset usage period and method.
    * Asset category. 
    * Asset method types
    * Default accounts for methods and categories
    * Depreciation methods:
        - Straight-Line
        - Declining-Balance
        - Sum of Year Digits
        - Units of Production - this method can be used for individual depreciation schedule.
        - Progressive
    * Method Parameters:
	- Starting interval (period)
	- Number of depreciation intervals
	- Number of intervals per year
	- Progressive factor for Declining-Balance method
	- Salvage Value
	- Life Quantity for Unit of Production method
    * Functionality:
	- Defining the asset in invoice when purchasing
	- Adjusting the asset value in purchasing Refund
	- Periodical entering of units of production
	- Periodical asset calculation
	- Sales invoice stops the depreciation and make final postings
    * Wizards:
	- Initial Values for continuing depreciation from previous system
	- Revaluation
	- Abandonment
	- Method parameters changing
	- Suppressing and Resuming depreciation
	- Localisation changing

This module is based on original Tiny module account_asset version 1.0 of the same name "Financial and accounting asset management".

Purpose of the module is to aid fixed assets management and integrate this management into the accounting system.

Terms used in the module:
- Asset - product or set of products which are used internally in company for longer time and must be taken into asset registry.
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
1. Create Asset categories in menu "Financial Management - Configuration - Assets - Asset Categories". Categories can be hierarchical. Read farther how hierarchy works for Method Defaults and for Periodical Calculation. You can review hierarchy of categories in menu "Financial Management - Configuration - Assets - Category Structure"

2. Create Method types in menu "Financial Management - Configuration - Assets - Asset Method Types". You should create method type for every kind of depreciation. Fe. you use fast depreciation for computer equipment and slow depreciation for buildings. You can also create different types for cost depreciation and for tax depreciation (if you use tax depreciation).

3. Create Method Defaults in menu "Financial Management - Configuration - Assets - Asset Method Defaults". You can create default settings for method type only or for pairs of method type and asset category. It is suggested to accounting manager to design asset categories hierarchy and assign defaults to categories and method types before system start. If it will be well designed accountants will have simplified and more error-proof job later on. All accounts, calculation methods and other parameters will be entered automatically during asset creation. Note that as Categories are hierarchical the defaults will work also hierarchical for all children categories. It means that if there is no defaults line for certain pair of Method Type and Category system look for pairs of Method Type and parent Category. It looks for such pair till root of Category.

4. Create asset in menu "Financial Management - Configuration - Assets - Assets" or in "Financial Management - Assets - Assets". In Asset form you should enter the name of asset, asset code (abbreviation or numerical symbol which can be set in Sequence settings). Then you select Asset category. It is optional step but it would be used to enter method defaults. 

Then you go to methods creation. Asset can have many methods. They can be used when asset is a set of several elements. Fe. Computer set consisting PC, screen and printer. When they have the same depreciation rule they can be in one method (invoice lines assigned to the same method). If they have different depreciation rules they have to be in different methods. 

As a first step in creation of method select Method Type. After Method Type selection many fields can be filled automatically. First system creates the method Name from Method Type Code, Asset name and Asset Code. It would simplify Method selection in invoice line. Then system fills other fields according to method type defaults. There are accounts, calculation methods and other values. You can change Method name and other default settings before asset saving but when you select Method type again (even to the same type) these fields will be reverted back to defaults.

5. As buying is the most common way to possess the asset you usually have to assign the created asset method to supplier invoice line. So when you create the draft supplier invoice you have to open the invoice line and select the created asset method. Notice that after method selection the invoice line account would be changed to Asset Account which was set in Asset method. Then when you create the invoice the asset state changes to Normal, Asset method state changes to Open and method is ready for depreciation.

When asset purchase is subject of refund and asset should change the value according to that you should assign Refund line to asset method as you did during Purchasing. Method value will be reflected to the refund value.

When an asset should consist few elements and these elements will be depreciated the same way (with the same rules) you can assignt few invoice lines to the same method. (From the same invoice or another). But if elements depreciation rules differs you should create separate methods for these elements.

6. To make asset calculation choose "Financial Management - Periodical Processing - Assets Calculation - Compute Assets". You have to select period of calculation and date of postings. Selected period is also used as posting period so Date must be in Period. Then you can select Asset Category and Method Type which you would like to compute. Remember that Categories are hierarchical and work for all children. 

7. When you possesed the asset different way than purchasing (by own production or investment) or you wish to continue depreciation started in other system you can use wizard Initial Values. If you continue depreciation you can enter:
    a. Base Value as starting Total.
    b. Expense Value as depreciation already made.
    c. Intervals Before as number of intervals already calculated.
You can also Enter Base Value only as Residual left from previous depreciation (don't enter Expense Value and Intervals Before in such case).

You can use this wizard also to make starting account move if asset was produced by you or is a result of investment recorded previously in other accounts.

Remember that Wizards allows you to make note about previous depreciation in history entry. You can use Notes field for that.

8. When asset is to be sold you can assign appropriate method to the Customer invoice line. System will make needed postings and stop the asset method.

9. If you wish to revalue the method you can use Revalue Method button. Select parameters for postings and for asset history.

10. If you wish to abandon the asset you can use Abandon Method button. Parameters in wizard are described in labels.

11. You can wish suppress or resume the depreciation. You can use Suppress and Resume buttons for that. If method has state "Suppressed" it is not calculated.

12. Some local rules require to trace the asset localisation. You can use for that the button "Change Localisation" on asset tab "Other Information". This wizard will change localisation text and make proper entry in asset history.

Remarks:
- All wizard actions are traced in Asset history. You can use Asset history as Asset registry.
- Period in Method is used as indication of starting interval. If you have monthly periods, Intervals per Year is 4 (quarterly) and you set period July or August the calculation will start on September anyway. Depreciation is calculated always in last period of interval. If you set Intervals per Year to 1 (yearly depreciation) system calculates asset in 4th quarter or in December. In last case it calculates depreciation for whole year. If you wish to calculate different interval in first December than in following Decembers you can try to change method parameters using Change Parameters wizard at appropriate moment.
- If you make mistake in depreciations or in wizard actions you can delete created accounting moves usual way in Financial menu. They are in draft state after creation so they can be deleted. You can recreate depreciation moves in Compute Asset wizard. Deleting the moves created by wizards doesn't delete asset history entries.
- You can also manually create account moves for special postings not covered by this module functionality. In such case you have to assign move lines to asset method. You can use this possibility to add tax depreciation: 
    a. Create special method type for tax. 
    b. Create tax method for asset.
    c. Create manually initial account move.
    d. Create account move lines with proper accounts for assets.
    e. Assign account move lines to asset method.
    f. Use periodical depreciation computing as usual.
  You can try to use Initial Values wizard instead of points c, d, e.

- Unit of Production method. If you are not satisfied with any calculation method functionality or you wish to have individual depreciation schedule for method you can adopt Unit of Production calculation method for that:
    a. Select Units of Production as Computation Method
    b. Enter 100 in Life Quantity in method.
    c. On Usage tab use Create Usage Line wizard to create usage entries for the method.
    d. Enter percentage values as usage entries.
Usage values can be entered in method tab Usage or in menu "Financial Management - Periodical Processing - Assets Calculation - Method Usage". Second method is recommended for use before every period computation.
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

