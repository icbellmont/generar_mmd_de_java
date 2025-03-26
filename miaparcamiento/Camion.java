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
public class Camion extends Vehiculo {
    private int numEjes;

    public Camion(String matricula, boolean conAbono, int numEjes) {
        super(matricula, conAbono);
        this.numEjes = numEjes;
    }

    public Camion(String matricula, boolean conAbono, int numEjes, LocalDateTime fechaEntrada) {
        super(matricula, conAbono, fechaEntrada);
        this.numEjes = numEjes;
    }

    @Override
    public double calcularImporte() {
        long minutos = java.time.Duration.between(fechaEntrada, LocalDateTime.now()).toMinutes();
        double importe = (numEjes <= 3) ? minutos * 4.5 / 60 : minutos * 6.5 / 60;

        if (conAbono) {
            importe *= 0.6;
        }

        return importe;
    }
}