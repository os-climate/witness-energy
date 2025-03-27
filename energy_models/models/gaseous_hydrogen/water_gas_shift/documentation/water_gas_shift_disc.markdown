# Water Gas Shift reaction

Water Gas Shift reaction involves reaction between carbon monoxyde ($CO$) and water over a suitable catalyst to enrich a syngas mixture mainly composed of hydrogen ($H_2$) and carbon monoxyde. In 1780, Italian physicist Felice Fontana discovered the water gas shift reaction, but its actual importance was realized much later.

The reaction can be used to enrich a syngas to obtain a given $CO$ to $H_2$ ratio for a specific technology (Fischer Tropsch reaction or methanol synthesis for example) or to produce $CO$-free hydrogen by cleaning $CO$ residues from syngas which are poisonous and deadly.

In order to achieve large-scale hydrogen production from syngas, an appropriate catalyst must be chosen to facilitate the reaction.


![](WGS_catalysts.PNG)
(Image Credit: Pal, D. [^1])

The figure above shows a broad classification of catalysts that have been commonly used for the WGS reaction. WGS catalysts may be divided into five categories: High-Temperature Catalysts, Low-Temperature Catalysts, Ceria and Noble Metal based Catalysts; Carbon based Catalysts and Nanostructured Catalysts. All processes to obtain the catalysts and a comparison of them can be found in [^1].

The syngas in the model is defined with a syngas ratio ($r_1$) which is the molar ratio of CO over $H_2$. The objective of the reaction is to eliminate the CO inside the syngas to obtain another syngas at a different molar ratio ($r_2$). With a zero $r_2$ ratio, the syngas is fully converted into hydrogen.

However, the reaction products carbon dioxyde ($CO_2$) which can be captured and stored with suitable technologies (see Carbon Capture and Storage technologies on flue gas).

The main reaction of this technology is :


$$(H_2 +r_1 CO) + cH_20 --> dCO_2 + e(H_2 +r_2CO)$$

with $r_1$ and $r_2$ syngas ratios before and after the reaction :

$$r_i = \frac{mol CO}{mol H2}$$

and with $c$,$d$ and $e$ coefficients of the reaction that can be computed with $r_1$ and $r_2$ to satisfy chemical equilibrium :

$$c = \frac{r1-r2}{1+r2}$$

$$d = r1 - \frac{r2(1+r1)}{1+r2}$$

$$e = \frac{1+r1}{1+r2}$$


## Data

Economic datas are computed following the work in [^2] where a techno-economic analysis is performed on a two-stage WGS combining Low-Temperature and High-Temperature catalysts.
Theoretical datas about production and consumption have been computed with coefficients above depending on $CO$ to $H_2$ ratios ($r_1$ and $r_2$). Other technical datas (i.e. construction delay, lifetime or learning rate, efficiency) can be found in [^2] or [^3].

The initial world production has

## Heat
[^4] WGSR is the reaction of an equimolar mixture of steam and carbon monoxide and the process is moderately exothermic.
It is an important step in the reforming process.

CO + O<sub>(a)</sub> → CO<sub>2</sub> + ∗  ....   ΔH°= −283kJ/mol

H<sub>2</sub>O + ∗ → H<sub>2</sub> + O<sub>(a)</sub> .... ΔH°= 242kJ/mol.

Combining the above two reactions gives WGSR.

CO + H<sub>2</sub>O → CO<sub>2</sub> + H<sub>2</sub>  .... ΔH°=−41kJ/mol


[^1]: Pal, D.B., Chand, R., Upadhyay, S.N. and Mishra, P.K., 2018. Performance of water gas shift reaction catalysts: A review. Renewable and Sustainable Energy Reviews, 93, pp.549-565.available at https://www.sciencedirect.com/science/article/pii/S1364032118303411

[^2]: Giuliano, A., Freda, C. and Catizzone, E., 2020. Techno-economic assessment of bio-syngas production for methanol synthesis: A focus on the water–gas shift and carbon capture sections. Bioengineering, 7(3), p.70. available at https://www.mdpi.com/2306-5354/7/3/70
[^3]: Wang, Y., Li, G., Liu, Z., Cui, P., Zhu, Z. and Yang, S., 2019. Techno-economic analysis of biomass-to-hydrogen process in comparison with coal-to-hydrogen process. Energy, 185, pp.1063-1075.
[^4]: https://www.sciencedirect.com/topics/engineering/water-gas-shift-reaction#:~:text=The%20water%E2%80%93gas%20shift%20reaction,the%20process%20is%20moderately%20exothermic.
