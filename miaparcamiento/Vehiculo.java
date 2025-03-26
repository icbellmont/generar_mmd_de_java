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

public abstract class Vehiculo {
    protected String matricula;
    protected LocalDateTime fechaEntrada;
    protected boolean conAbono;

    public Vehiculo(String matricula, boolean conAbono) {
        this.matricula = matricula;
        this.conAbono = conAbono;
        this.fechaEntrada = LocalDateTime.now();
    }

    public Vehiculo(String matricula, boolean conAbono, LocalDateTime fechaEntrada) {
        this.matricula = matricula;
        this.conAbono = conAbono;
        this.fechaEntrada = fechaEntrada;
    }

    public abstract double calcularImporte();

    public String getMatricula() {
        return matricula;
    }

    public LocalDateTime getFechaEntrada() {
        return fechaEntrada;
    }

    public boolean isConAbono() {
        return conAbono;
    }
}