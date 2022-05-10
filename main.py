import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
plt.style.use ('classic')

class Energibehov:
    def __init__(self):
        self.profet_data = pd.read_csv('Effektprofiler.csv', sep=';')
        
    def hent_profil(self, bygningstype, bygningsstandard, forbrukstype, areal):
        
        bygningstype, bygningsstandard, forbrukstype, areal = self.input_data(bygningstype, bygningsstandard, forbrukstype, areal)
        
        if forbrukstype == 'Space_heating_og_DHW':
            return areal * (np.array(self.profet_data[bygningstype + bygningsstandard + 'Space_heating']) + np.array(self.profet_data[bygningstype + bygningsstandard + 'DHW']))
        else:
            return areal * np.array(self.profet_data[bygningstype + bygningsstandard + forbrukstype])
            
    def input_data(self, bygningstype, bygningsstandard, forbrukstype, areal):
        bygningstype = bygningstype.upper()
        bygningsstandard = bygningsstandard.upper()
        forbrukstype = forbrukstype.upper()

        bygningstyper = {
            'A' : 'House', 
            'B' : 'Apartment', 
            'C' : 'Office', 
            'D' : 'Shop', 
            'E' : 'Hotel',
            'F' : 'Kindergarten',
            'G' : 'School', 
            'H' : 'University',
            'I' : 'Culture_Sport', 
            'J' : 'Nursing_Home',
            'K' : 'Hospital',
            'L' : 'Other', 
        }
        bygningsstandarder = {
            'X' : 'Regular',
            'Y' : 'Efficient',
            'Z' : 'Very efficient',
        }
        forbrukstyper = {
            '1' : 'Electric',
            '2' : 'DHW',
            '3' : 'Space_heating',
            '4' : 'Cooling',
            '5' : 'Space_heating_og_DHW',
        }
        return bygningstyper[bygningstype], bygningsstandarder[bygningsstandard], forbrukstyper[forbrukstype], areal



class Dimensjonering:
    def __init__(self, energibehov_h, COP, DEKNINGSGRAD, MAKS_BRONNDYBDE):
        self.totalt_energibehov_h = energibehov_h
        self.totalt_energibehov_y = round (sum (energibehov_h))
    
        self.COP = COP
        self.DEKNINGSGRAD = DEKNINGSGRAD
        self.MAKS_BRONNDYBDE = MAKS_BRONNDYBDE
        
        self.energi_og_effekt_beregning ()
    
    def energi_og_effekt_beregning (self): 
        varmepumpe_storrelse = max(self.totalt_energibehov_h)
        beregnet_dekningsgrad = 100.5
        
        while (beregnet_dekningsgrad / self.DEKNINGSGRAD) > 1:
            tmp_liste_h = np.zeros (8760)
            for i, timeverdi in enumerate (self.totalt_energibehov_h):
                if timeverdi > varmepumpe_storrelse:
                    tmp_liste_h[i] = varmepumpe_storrelse
                else:
                    tmp_liste_h[i] = timeverdi
            
            beregnet_dekningsgrad = (sum (tmp_liste_h) / self.totalt_energibehov_y) * 100

            varmepumpe_storrelse -= 0.05
                           
        self.grunnvarme_energibehov_h = np.array (tmp_liste_h)
        self.grunnvarme_energibehov_y = round (np.sum (tmp_liste_h))
        self.varmepumpe_storrelse = float("{:.1f}".format(varmepumpe_storrelse))
        self.beregnet_dekningsgrad = float("{:.0f}".format(beregnet_dekningsgrad))
                      
    #Timer
    def levert_energi_h (self):
        return self.grunnvarme_energibehov_h - self.grunnvarme_energibehov_h / self.COP   
        
    def kompressor_energi_h (self):
        return self.grunnvarme_energibehov_h - self.levert_energi_h ()
        
    def spisslast_energi_h (self):
        return self.totalt_energibehov_h - self.grunnvarme_energibehov_h
    
    #Årlig 
    def levert_energi_y (self):
        return int(sum (self.levert_energi_h ()))
        
    def kompressor_energi_y (self):
        return int(sum (self.kompressor_energi_h ()))
        
    def spisslast_energi_y (self):
        return int(sum (self.spisslast_energi_h ()))
    
    #Dimensjonering av antall brønnmeter - denne er veldig enkel foreløpig og kan utvides senere med for eksempel https://github.com/MassimoCimmino/pygfunction biblioteket
    def antall_meter (self):
        energi_per_meter = 80  # kriterie 1
        effekt_per_meter = 30  # kriterie 2
        
        antall_meter_effekt = ((self.varmepumpe_storrelse - self.varmepumpe_storrelse / self.COP) * 1000) / effekt_per_meter
        antall_meter_energi = (self.levert_energi_y ()) / energi_per_meter

        if antall_meter_effekt < antall_meter_energi:
            antall_meter_tot = antall_meter_energi
        else:
            antall_meter_tot = antall_meter_effekt
        return round(antall_meter_tot) 
    
    #Antall brønner 
    def antall_bronner(self):
        antall_m = self.antall_meter()
        bronndybde = 0
        for i in range(1,10):
            bronndybde += self.MAKS_BRONNDYBDE
            if antall_m <= bronndybde:
                return i
    
    def varighetsdiagram (self):
        x_arr = np.array (range (0, len (self.totalt_energibehov_h)))
        plt.fill_between (x_arr, np.sort (self.totalt_energibehov_h) [::-1], label = 'Spisslast (dekkes ikke av grunnvarme)', color = '#F0F4E3') #Sorterte timeverdier fra max -> min
        plt.fill_between (x_arr, np.sort (self.grunnvarme_energibehov_h) [::-1], label = 'Levert energi fra brønn(er)', color ='#48a23f') #Sorterte timeverdier fra max -> min
        plt.fill_between (x_arr, np.sort (self.kompressor_energi_h ()) [::-1], label = 'Energiforbruk varmepumpe (strøm)', color = '#1d3c34') #Sorterte timeverdier fra max -> min
        plt.grid()
        plt.xlim (0, 8760)
        plt.ylim (0, max(self.totalt_energibehov_h))
        plt.title(f'Effektvarighetsdiagram som illustrerer\n hvor stor andel av energien som dekkes av en gitt effekt.\n \
        I dette tilfellet; En varmepumpe på {self.varmepumpe_storrelse} kW dekker {self.DEKNINGSGRAD} % av energien.')
        plt.xlabel ('Varighet [timer]')
        plt.ylabel ('Effekt [kW]')
        plt.legend ()
        plt.show()
        plt.close ()
        
    def dekningsgrad_diagram (self):
        x_arr = np.array (range (0, len (self.totalt_energibehov_h)))
        plt.plot (x_arr, self.totalt_energibehov_h, label = 'Totalt energibehov')
        plt.plot (x_arr, self.grunnvarme_energibehov_h, label = ('90% dekning med varmepumpe = ' + str (self.varmepumpe_storrelse) + ' kW'))
        plt.title ('Cutoff')
        plt.xlabel ('Timeverdier')
        plt.ylabel ('kW')
        plt.legend ()
        plt.show()
        plt.close ()
        
    def standard_dimensjonering (self):
        print (f'Totalt energibehov er {self.totalt_energibehov_y} kWh')
        print (f'Energibehovet som skal dekkes av grunnvarmeanlegget er {self.grunnvarme_energibehov_y} kWh')
        print (f'Dette tilsvarer {self.beregnet_dekningsgrad} % av det totale energibehovet')
        print ('\n')
        print (f'Av energibehovet som skal dekkes av grunnvarmeanlegget er: \n' 
               f'{self.levert_energi_y ()} kWh levert fra brønnene \n'
               f'{self.kompressor_energi_y ()} kWh fra kompressoren \n'
               f'{self.spisslast_energi_y()} kWh til spisslast')
        print ('\n')
        print ('Disse resultatene er også fremstilt i varighetsdiagrammet under: ')
        self.varighetsdiagram ()
        print (f'For å dekke dette energibehovet bør totalt antall brønnmetere være {self.antall_meter ()} \n'
               f'Varmepumpen bør være på {self.varmepumpe_storrelse} kW \n'
               f'Antall brønner bør være {self.antall_bronner()}')
        
#Eksempelkjøring 
COP, DEKNINGSGRAD, MAKS_BRONNDYBDE = 3.3, 90, 350 #Standardverdier - dekke kan også varieres etter brukerinput. For eksempel COP i intervallet [2 - 4], dekningsgrad [80 - 100 %] og maks brønndybde [250 - 350 m]
bygg1 = Energibehov()
timeserie_bygg1 = bygg1.hent_profil('A', 'X', '3', 2000)

enkelt_anlegg = Dimensjonering (timeserie_bygg1, COP, DEKNINGSGRAD, MAKS_BRONNDYBDE)
enkelt_anlegg.standard_dimensjonering()