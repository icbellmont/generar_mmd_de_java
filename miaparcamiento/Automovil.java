/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package com.mycompany.miaparcamiento;

import java.time.LocalDateTime;

/**
 *
 * @author i60r
 */
public class Automovil extends Vehiculo {
    public enum Tipo { TURISMO, TODOTERRENO, FURGONETA } // Definición de la enumeración
    private Tipo tipo;

    public Automovil(String matricula, boolean conAbono, Tipo tipo) {
        super(matricula, conAbono);
        this.tipo = tipo;
    }

    public Automovil(String matricula, boolean conAbono, Tipo tipo, LocalDateTime fechaEntrada) {
        super(matricula, conAbono, fechaEntrada);
        this.tipo = tipo;
    }

    @Override
    public double calcularImporte() {
        long minutos = java.time.Duration.between(fechaEntrada, LocalDateTime.now()).toMinutes();
        double importe = 0;

        switch (tipo) {
            case TURISMO:
                importe = minutos * 1.5 / 60;
                break;
            case TODOTERRENO:
                importe = minutos * 2.5 / 60;
                break;
            case FURGONETA:
                importe = minutos * 3.5 / 60;
                break;
        }

        if (conAbono) {
            importe *= 0.6;
        }

        return importe;
    }
}