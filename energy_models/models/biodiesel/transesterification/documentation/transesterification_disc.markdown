# First Generation Biofuel, FAME Biodiesel

## What is Biodiesel?
The major components of vegetable oils and animal fats are triacylglycerols (often also called triglycerides). Chemically, triacylglycerols are esters of fatty acids with glycerol.
For obtaining biodiesel, the vegetable oil or animal fat is subjected to a chemical reaction termed transesterification. In that reaction, the vegetable oil or animal fat is reacted in the presence of a catalyst (usually Sodium Hydroxide or Potassium Hydroxide) with an alcohol (usually methanol) to give the corresponding alkyl esters (when using methanol, the methyl esters) of the fatty acid mixture that is found in the parent vegetable oil or animal fat.
Biodiesel can be produced from a great variety of feedstocks. These feedstocks include most common vegetable oils (soybean, cottonseed, palm, peanut, rapeseed /canola, sunfl ower, saffl ower, coconut, etc.) and animal fats (usually tallow) as well as waste oils (used frying oils, etc.). Which feedstock is used depends largely on geography.
Biodiesel is miscible with petrodiesel in all ratios. This has led to the use of blends of biodiesel with petrodiesel instead of neat biodiesel in many countries. It is important to note that blending with petrodiesel is not biodiesel. Often blends with petrodiesel are denoted by acronyms such as B20 which is a blend of 20% biodiesel with petrodiesel.[^1]



![](biodiesel.jpg)
(Image Credit: VTT Studio/Shutterstock.com)


## **Transesterification**
The transesterification reaction is the following:

![](transesterification_formula.png)

The transesterification process with typical input and output quantities is as follow:

```mermaid
graph TB %% comments
  %% Entity[Text]
  ID-1([Refined Vegetable oil/<br>Animal Fat/<br>Waste oil])
  ID-2([Methanol])
  ID-3([Catalyst<br>NaOH/KOH])
  ID-4([Glycerol])
  ID-5[(Transesterification)]
  ID-6(Crude Biodiesel)
  ID-7["Washed, Dryed and Filtered"]
  ID-8(FAME<br>Biodiesel)
  ID-9([Water])
  ID-10([Electricity])
  %% Entity--Entity
  ID-5 --> ID-6
  ID-6 --> ID-7

  %% Entity--Text--Entity
  ID-1-->|1000kg|ID-5
  ID-2-->|107kg|ID-5
  ID-3-->|10kg|ID-5
  ID-10-->|20kWh|ID-5
  ID-5-->|125kg|ID-4
  ID-9-->|17kg|ID-7
  ID-7-->|1000kg|ID-8



```

Methanol is used as alcohol for producing biodiesel because it is the least expensive alcohols, for example ethanol or iso-propanol, may afford a biodiesel fuel with better fuel properties. Often the resulting product is also called FAME (fatty acid methyl esters) instead of biodiesel. Although other alcohols can by definition give biodiesel, many now existing standards are designed in such a fashion that only methyl esters can be used as biodiesel when observing the standards.

## Advantages & Problems
Biodiesel has several distinct advantages compared to petrodiesel besides being fully competitive with petrodiesel in most technical aspects:
* Derived from a renewable domestic resource, thus reducing dependence on and preserving petroleum.
* Biodegradability.
* Reduces most regulated exhaust emissions (with the exception of nitrogen oxides,
NOx ).
* Higher flash point leading to safer handling and storage.
* Excellent lubricity. This fact is steadily gaining significance with the advent of low-sulfur petrodiesel fuels, which have significantly reduced lubricity. Adding biodiesel at low levels (1-2%) restores the lubricity.

Some problems associated with biodiesel are its inherent higher price, which in many countries is offset by legislative and regulatory incentives or subsidies in the form of reduced excise taxes, slightly increased NOx exhaust emissions, stability when exposed to air (oxidative stability), and cold flow properties. The higher price can also be (partially) offset by the use of less expensive feedstocks which has sparked the interest in materials such as waste oils (for example, used frying oils).

## Use in Jet Fuel
Biodiesel have also a potential to be used as a blending agent in jetfuel because certain FAME molecules can fit the jetfuel fuel performance criteria if fractionated. It is still a research area and not mature yet.

## Data
Generic information regarding [biodiesel](https://en.wikipedia.org/wiki/Biodiesel) and [transesterification](https://en.wikipedia.org/wiki/Transesterification) are coming from Wikipedia.

Specific information regarding transesterification process comes from The Biodiesel Handbook
Second Edition, AOCS, 2010[^1]

Data regarding prices of vegetable oil and reference biodiesel price are coming from [Neste website](https://www.neste.com/investors/market-data/palm-and-rapeseed-oil-prices)

Global investments on biodiesel is extracted from the World Energy Investment 2020 from IEA

Transesterification process input and outputs quantities are coming from [IEA Advanced Motor Fuels Implementing Agreement, Final Report - Analysis of Biodiesel Options, Annex XXXIV: Biomass-Derived Diesel Fuels, p54](https://www.iea-amf.org/app/webroot/files/file/Annex%20Reports/AMF_Annex_34-1.pdf)

Fuel properties (calorific values, density) are coming from [Engineering Toolbox](https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html)

Technico-economic information (Capex, Opex) are coming from [Biodiesel production through sulfuric acid catalyzed transesterification of acidic oil: Techno economic feasibility of different process alternatives](https://nmbu.brage.unit.no/nmbu-xmlui/bitstream/handle/11250/2690185/Article69327.pdf?sequence=2)

[^1]: Biodiesel Handbook (2010), AOCS Press

