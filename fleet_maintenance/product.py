from osv import fields,osv

class product_template(osv.osv):
    _inherit = "product.template"
    
    _columns = {
        "is_maintenance" : fields.boolean('Is Maintenance?'),
        "maintenance_analytic_id" : fields.many2one('account.analytic.account', 'Maintenance Analytic Account'),
    }
    
product_template()
