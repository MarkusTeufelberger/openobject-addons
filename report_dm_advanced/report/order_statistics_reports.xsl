<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:fo="http://www.w3.org/1999/XSL/Format">

	<xsl:template match="/">
		<xsl:call-template name="rml" />
	</xsl:template>

	<xsl:template name="rml">
        <document filename="example.pdf">
            <!--template pageSize="45cm,21cm" title="Test" author="Martin Simon" allowSplitting="20"-->
            <template>
                <xsl:attribute name="pageSize">
                    <xsl:value-of select="/report/cols/attribute::templatewidth"/>
                </xsl:attribute>
                <xsl:attribute name="title">Test</xsl:attribute>
                <xsl:attribute name="author">Martin Simon</xsl:attribute>
                <xsl:attribute name="allowSplitting">20</xsl:attribute>
                <pageTemplate id="first">
                    <frame>
                        <xsl:attribute name="id">first</xsl:attribute>
                        <xsl:attribute name="x1">2cm</xsl:attribute>
                        <xsl:attribute name="y1">2.5cm</xsl:attribute>
                        <xsl:attribute name="width">
                            <xsl:value-of select="/report/cols/attribute::framewidth"/>
                        </xsl:attribute>
                        <xsl:attribute name="height">17cm</xsl:attribute>
                    </frame>
    			</pageTemplate>
			</template>

			<stylesheet>
				<paraStyle name="normal" fontName="Helvetica" fontSize="6" alignment="center" />
				<paraStyle name="normal-title" fontName="Helvetica" fontSize="6" />
				<paraStyle name="title" fontName="Helvetica" fontSize="18" alignment="center" />
				<paraStyle name="date" fontName="Helvetica-Oblique" fontSize="10" textColor="blue" />
				<paraStyle name="glande" textColor="red" fontSize="7" fontName="Helvetica"/>
				<paraStyle name="normal_people" textColor="green" fontSize="7" fontName="Helvetica"/>
				<paraStyle name="esclave" textColor="purple" fontSize="7" fontName="Helvetica"/>
				<blockTableStyle id="month">
					<!--blockAlignment value="CENTER" start="1,0" stop="-1,-1" /-->
					<blockFont name="Helvetica" size="8" start="0,0" stop="-1,1"/>
					<blockFont name="Helvetica" size="6" start="0,2" stop="-2,-2"/>
					<blockFont name="Helvetica-BoldOblique" size="8" start="0,-1" stop="-1,-1"/>
					<lineStyle kind="LINEABOVE" colorName="black" start="0,0" stop="-1,-1" />
					<lineStyle kind="LINEBEFORE" colorName="black" start="0,0" stop="-1,-1"/>
					<lineStyle kind="LINEAFTER" colorName="black" start="-1,0" stop="-1,-1"/>
					<lineStyle kind="LINEBELOW" colorName="black" start="0,-1" stop="-1,-1"/>
					<blockValign value="TOP"/>
				</blockTableStyle>
			</stylesheet>

			<xsl:call-template name="story"/>
		</document>
	</xsl:template>

	<xsl:template name="story">
		<xsl:for-each select="report/story">	
		<xsl:variable name="s_id" select="attribute::s_id"/>
		<story>
		    <para style="title" t="1"> <xsl:value-of select="attribute::name"/> </para>
            <spacer length="1cm" />
		    <blockTable>
			    <xsl:attribute name="style">month</xsl:attribute>
                <xsl:attribute name="colWidths"><xsl:value-of select="//cols" /></xsl:attribute>
			    <tr>
                    <td>
                        <xsl:value-of select="//date/attribute::from_month_year" /> -
                        <xsl:value-of select="//date/attribute::to_month_year" /></td>
				    <xsl:for-each select="//days/day">
					    <td>
						    <xsl:value-of select="attribute::string" />
					    </td>
				    </xsl:for-each>
				    <td t="1">Total</td>
			    </tr>
			    <xsl:apply-templates select="row"/>
			    <xsl:for-each select="row">
				    <xsl:variable name="id" select="attribute::id"/>
				    <tr>
					    <td><para><xsl:value-of select="attribute::name"/></para></td>
					    <xsl:for-each select="//report/days/day">
					    <xsl:variable name="today" select="attribute::number" />
                            <td>
                                <para>
								     <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element[@date=$today]), '##.##')" />
							    </para>
						    </td>
					    </xsl:for-each>
					    <td>
					        <para> 
            				     <xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row[@id=$id]/time-element),'##.##')"/>
        					</para>
					    </td>
				    </tr>
			    </xsl:for-each>
			    <tr>
				    <td t="1">Total</td>
				    <xsl:for-each select="//report/days/day">
					    <xsl:variable name="today" select="attribute::number"/>
					    <td>
                        <para><xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element[@date=$today]),'##.##')"/></para>
					    </td>
				    </xsl:for-each>
				    <td><xsl:value-of select="format-number(sum(//story[@s_id=$s_id]/row/time-element),'##.##')"/></td>
			    </tr>
            </blockTable>
    	</story>
	</xsl:for-each>
	
	</xsl:template>
</xsl:stylesheet>
