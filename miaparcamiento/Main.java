/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package com.mycompany.miaparcamiento;

/**
 *
 * @author i60r
 */
import java.time.LocalDateTime;

public class Main {
    public static void main(String[] args) {
        MiAparcamiento aparcamiento = new MiAparcamiento(10);

        Automovil auto1 = new Automovil("1234ABC", false, Automovil.Tipo.TURISMO);
        Camion camion1 = new Camion("5678DEF", true, 4);

        aparcamiento.introducirVehiculo(auto1);
        aparcamiento.introducirVehiculo(camion1);

        // Simulamos que han pasado 120 minutos
        LocalDateTime fechaSalida = LocalDateTime.now().plusMinutes(120);
        Automovil auto2 = new Automovil("9101GHI", true, Automovil.Tipo.FURGONETA, fechaSalida);
        aparcamiento.introducirVehiculo(auto2);

        System.out.println("Importe auto1: " + aparcamiento.sacarVehiculo(auto1));
        System.out.println("Importe camion1: " + aparcamiento.sacarVehiculo("5678DEF"));
        System.out.println("Importe auto2: " + aparcamiento.sacarVehiculo(auto2));
    }
}