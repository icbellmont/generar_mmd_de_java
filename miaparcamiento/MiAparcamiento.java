/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 */

package com.mycompany.miaparcamiento;

/**
 *
 * @author i60r
 */
import java.util.ArrayList;

public class MiAparcamiento {
    private ArrayList<Vehiculo> vehiculos;
    private int capacidad;

    public MiAparcamiento(int capacidad) {
        this.capacidad = capacidad;
        this.vehiculos = new ArrayList<>();
    }

    public boolean introducirVehiculo(Vehiculo v) {
        if (vehiculos.size() < capacidad && !vehiculos.contains(v)) {
            vehiculos.add(v);
            capacidad--;
            return true;
        }
        return false;
    }

    public double sacarVehiculo(Vehiculo v) {
        if (vehiculos.remove(v)) {
            capacidad++;
            return v.calcularImporte();
        }
        return -1;
    }

    public double sacarVehiculo(String matricula) {
        for (Vehiculo v : vehiculos) {
            if (v.getMatricula().equals(matricula)) {
                vehiculos.remove(v);
                capacidad++;
                return v.calcularImporte();
            }
        }
        return -1;
    }
}