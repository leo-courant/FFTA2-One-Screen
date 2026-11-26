// Ghidra headless post-script: write every reference that lands on a function
// entry (calls, jumps, and pointers stored in data or literal pools) as TSV.
// Usage: see scripts/decomp_index.sh. Arg 0 = output TSV path, arg 1 = optional
// file of function entry addresses (one 0x... per line) to create if missing.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class ExportXrefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        FunctionManager fm = currentProgram.getFunctionManager();
        if (args.length > 1) {
            int made = 0;
            for (String line : Files.readAllLines(Paths.get(args[1]))) {
                line = line.trim();
                if (!line.startsWith("0x")) continue;
                Address a = toAddr(Long.decode(line));
                if (fm.getFunctionAt(a) == null) {
                    disassemble(a);
                    if (createFunction(a, null) != null) made++;
                }
            }
            println("created " + made + " missing functions");
        }
        ReferenceManager rm = currentProgram.getReferenceManager();
        Listing listing = currentProgram.getListing();
        try (PrintWriter out = new PrintWriter(new FileWriter(args[0]))) {
            out.println("target\tfrom\tfrom_func\tkind");
            for (Function f : fm.getFunctions(true)) {
                Address entry = f.getEntryPoint();
                for (Reference r : rm.getReferencesTo(entry)) {
                    Address from = r.getFromAddress();
                    Function ff = fm.getFunctionContaining(from);
                    RefType t = r.getReferenceType();
                    String kind = t.isCall() ? "call" : t.isJump() ? "jump"
                                : t.isData() ? "pointer" : t.toString();
                    if (kind.equals("pointer") && listing.getInstructionAt(from) == null
                            && ff == null) kind = "table";
                    out.println(entry + "\t" + from + "\t"
                                + (ff == null ? "-" : ff.getEntryPoint().toString()) + "\t" + kind);
                }
            }
        }
        println("functions: " + fm.getFunctionCount());
    }
}
