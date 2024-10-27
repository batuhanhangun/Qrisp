"""
\********************************************************************************
* Copyright (c) 2024 the Qrisp authors
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* This Source Code may also be made available under the following Secondary
* Licenses when the conditions for such availability set forth in the Eclipse
* Public License, v. 2.0 are satisfied: GNU General Public License, version 2
* with the GNU Classpath Exception which is
* available at https://www.gnu.org/software/classpath/license.html.
*
* SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0
********************************************************************************/
"""

from qrisp.operators.fermionic.visualization import a_,c_

#
# FermionicTerm
#

import numpy as np

class FermionicTerm:
    r"""
    
    """

    def __init__(self, ladder_list=[]):
        
        # Sort ladder operators (ladder operator semantics are order in-dependent)
        participating_indices = [index for index, is_creator in ladder_list]
        ladder_list = [ladder_list[i] for i in np.argsort(participating_indices)]
        
        self.ladder_list = ladder_list
        
        # Compute the hash value such that 
        # terms receive the same hash as their hermitean conjugate
        # this way the FermionicHamiltonian does not have
        # to track both the term and it's dagger
        index_list = [index for index, is_creator in ladder_list]
        is_creator_temp_hash = 0
        for i in range(len(ladder_list)):
            is_creator_temp_hash += ladder_list[i][1]*2**i
            
        is_creator_hash = (2**len(ladder_list) - 1 - is_creator_temp_hash)*is_creator_temp_hash
        
        self.hash_value = hash(tuple(index_list + [is_creator_hash]))

    #def update(self, update_dict):
    #    self.pauli_dict.update(update_dict)
    #    self.hash_value = hash(tuple(sorted(self.pauli_dict.items())))

    def __hash__(self):
        return self.hash_value

    def __eq__(self, other):
        return self.hash_value == other.hash_value
    
    def copy(self):
        return FermionicTerm(self.ladder_list.copy())
    
    def dagger(self):
        return FermionicTerm([(index, not is_creator) for index, is_creator in self.ladder_list])
    #
    # Printing
    #

    def __str__(self):
        # Convert the sympy expression to a string and return it
        expr = self.to_expr()
        return str(expr)

    def to_expr(self):
        """
        Returns a SymPy expression representing the FermionicTerm.

        Returns
        -------
        expr : sympy.expr
            A SymPy expression representing the FermionicTerm.

        """

        def to_ladder(value, index):
            if value:
                return c_(index)
            else:
                return a_(index)
        
        expr = 1
        for index,value in self.ladder_list:
            expr *= to_ladder(value,str(index))

        return expr

    #
    # Arithmetic
    #

    def __mul__(self, other):
        result_ladder_list = self.ladder_list + other.ladder_list
        return FermionicTerm(result_ladder_list)
    
    def order(self):
        """
        Not that important, since relevant Hamiltonians (e.g., electronic structure) consist of ordered terms.
        What is needed for trotterization?

        Fermionic commutation relations:

        {a_i,a_j^dagger} = a_i*a_j^dagger + a_j^dagger*a_i = delta_{ij}
        {a_i^dagger,a_j^dagger} = {a_i,a_j} = 0


        Order ladder terms such that 
            1) Raising operators preceed lowering operators
            2) Operators are ordered in descending order of fermionic modes

        Example: a_5^dagger a_2^dagger a_3 a_1

        """
        pass
    
    
    def simulate(self, coeff, qv):
        
        from qrisp import h, cx, rz, conjugate, control, QuantumBool, mcx
        
        def ghz_state(qb_list):
            for qb in qb_list[:-1]:
                cx(qb_list[-1], qb)
            h(qb_list[-1])
        
        participating_indices = [index for index, is_creator in self.ladder_list]
        participating_qubits = [qv[index] for index in participating_indices]
        ctrl_state = "".join([str(int(not is_creator)) for index, is_creator in self.ladder_list])
        
        phase_flipping_qubits = []
        
        while participating_indices:
            start = participating_indices.pop(0) + 1
            stop = participating_indices.pop(0)
            for i in range(start, stop):
                phase_flipping_qubits.append(qv[i])
                
        def flip_anchor_qubit(phase_flipping_qubits, anchor_qb):
            for qb in phase_flipping_qubits:
                cx(phase_flipping_qubits, anchor_qb)
        
        anchor_qubit = participating_qubits[-1]
        
        hs_ancilla = QuantumBool()
        with conjugate(ghz_state)(participating_qubits):
            with conjugate(flip_anchor_qubit)(phase_flipping_qubits, anchor_qubit):
                with conjugate(mcx)(participating_qubits[:-1], hs_ancilla, ctrl_state = ctrl_state[:-1], method = "gray_pt"):
                    with control(hs_ancilla):
                        if ctrl_state[0] == "0":
                            rz(coeff, anchor_qubit)
                        else:
                            rz(-coeff, anchor_qubit)
                
        hs_ancilla.delete()
                    

                
            
            
            
        
        
    
